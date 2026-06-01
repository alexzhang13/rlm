from collections.abc import Callable, Sequence
from typing import Any

QueryFn = Callable[[list[str], str | None], list[str]]


class AdaptiveRuntime:
    """Small runtime for batching independent sub-call frontiers.

    The runtime deliberately stays thin: it wraps the existing
    ``llm_query_batched`` / ``rlm_query_batched`` functions exposed by the REPL,
    adds a simple DAG frontier scheduler, and records lightweight metrics the
    model can inspect with ``adaptive_stats()``.
    """

    def __init__(
        self,
        llm_query_batched: QueryFn,
        rlm_query_batched: QueryFn,
        max_batch_size: int,
    ) -> None:
        self.llm_query_batched = llm_query_batched
        self.rlm_query_batched = rlm_query_batched
        self.max_batch_size = max(1, max_batch_size)
        self.metrics: dict[str, Any] = {
            "enabled": True,
            "topologies": [],
            "scheduled_prompts": 0,
            "batch_waves": 0,
            "wave_sizes": [],
            "items_processed": 0,
            "search_stages": 0,
            "candidates_scored": 0,
            "search_top_k": [],
        }

    def adaptive_batch(
        self,
        prompts: Sequence[str],
        query: str = "llm",
        model: str | None = None,
        batch_size: int | None = None,
    ) -> list[str]:
        """Run prompts through the selected batched query helper in waves."""
        prompt_list = [str(prompt) for prompt in prompts]
        if not prompt_list:
            return []

        batch_size = self.normalize_batch_size(batch_size)
        query_fn = self.get_query_fn(query)
        results: list[str] = []

        self.record_topology("adaptive_batch")
        self.metrics["scheduled_prompts"] += len(prompt_list)

        for start in range(0, len(prompt_list), batch_size):
            wave = prompt_list[start : start + batch_size]
            self.metrics["batch_waves"] += 1
            self.metrics["wave_sizes"].append(len(wave))
            results.extend(query_fn(wave, model))

        return results

    def adaptive_map(
        self,
        items: Sequence[Any],
        prompt_fn: Callable[[list[Any], int], str],
        items_per_prompt: int = 1,
        query: str = "llm",
        model: str | None = None,
        batch_size: int | None = None,
        parse_fn: Callable[[str], Any] | None = None,
        flatten: bool = False,
    ) -> list[Any]:
        """Pack items into prompt chunks, batch them, and optionally parse results.

        ``prompt_fn`` always receives ``(batch_items, start_index)``. For
        one-item prompts, ``batch_items`` is still a one-element list so the
        call signature stays predictable for model-written code.
        """
        item_list = list(items)
        if not item_list:
            return []
        if items_per_prompt <= 0:
            raise ValueError("items_per_prompt must be positive")

        self.record_topology("adaptive_map")
        self.metrics["items_processed"] += len(item_list)

        prompts = []
        for start in range(0, len(item_list), items_per_prompt):
            batch_items = item_list[start : start + items_per_prompt]
            prompts.append(prompt_fn(batch_items, start))

        responses = self.adaptive_batch(
            prompts,
            query=query,
            model=model,
            batch_size=batch_size,
        )
        if parse_fn is None:
            return responses

        parsed = [parse_fn(response) for response in responses]
        if not flatten:
            return parsed

        flattened: list[Any] = []
        for value in parsed:
            if isinstance(value, list):
                flattened.extend(value)
            else:
                flattened.append(value)
        return flattened

    def adaptive_dag(
        self,
        nodes: Sequence[dict[str, Any]],
        query: str = "llm",
        model: str | None = None,
        batch_size: int | None = None,
    ) -> dict[str, str]:
        """Execute a small dependency DAG layer by layer.

        Nodes support either ``prompt`` or ``prompt_template``. Templates are
        rendered with prior node answers by id, e.g. ``{node_a}``.
        """
        self.record_topology("adaptive_dag")
        remaining = {str(node["id"]): dict(node) for node in nodes}
        answers: dict[str, str] = {}

        while remaining:
            ready_ids = [
                node_id
                for node_id, node in remaining.items()
                if all(str(dep) in answers for dep in node.get("deps", []))
            ]
            if not ready_ids:
                unresolved = {
                    node_id: [str(dep) for dep in node.get("deps", [])]
                    for node_id, node in remaining.items()
                }
                raise ValueError(f"adaptive_dag could not resolve dependencies: {unresolved}")

            prompts = [
                self.render_node_prompt(remaining[node_id], answers) for node_id in ready_ids
            ]
            responses = self.adaptive_batch(
                prompts,
                query=query,
                model=model,
                batch_size=batch_size,
            )
            for node_id, response in zip(ready_ids, responses, strict=True):
                answers[node_id] = response
                del remaining[node_id]

        return answers

    def adaptive_search_tree(
        self,
        candidates: Sequence[Any],
        query: str,
        score_prompt_fn: Callable[[Any, int, str], str],
        parse_score_fn: Callable[[str, Any, int], dict[str, Any]],
        top_k: int = 20,
        stages: int = 1,
        expand_fn: Callable[[Any, dict[str, Any]], Sequence[Any] | None] | None = None,
        extract_prompt_fn: Callable[[Any, dict[str, Any], str], str] | None = None,
        batch_size: int | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Score and narrow a large candidate set in batched search stages.

        This helper is for sparse-evidence tasks over documents, chunks, files,
        or sections. It keeps the model in charge of scoring/parsing prompts but
        owns the repeated score -> top-k -> optional expansion scheduling loop.
        """
        candidate_list = list(candidates)
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        if stages <= 0:
            raise ValueError("stages must be positive")

        self.record_topology("adaptive_search_tree")
        stage_summaries: list[dict[str, Any]] = []
        top_results: list[dict[str, Any]] = []

        for stage_index in range(stages):
            if not candidate_list:
                break

            self.metrics["search_stages"] += 1
            self.metrics["candidates_scored"] += len(candidate_list)
            self.metrics["search_top_k"].append(top_k)

            prompts = [
                score_prompt_fn(candidate, index, query)
                for index, candidate in enumerate(candidate_list)
            ]
            responses = self.adaptive_batch(prompts, model=model, batch_size=batch_size)

            scored = [
                self.normalize_search_result(
                    parse_score_fn(response, candidate, index),
                    response,
                    candidate,
                    index,
                )
                for index, (candidate, response) in enumerate(
                    zip(candidate_list, responses, strict=True)
                )
            ]
            scored.sort(key=lambda result: result["score"], reverse=True)
            top_results = scored[:top_k]
            stage_summaries.append(
                {
                    "stage": stage_index,
                    "num_candidates": len(candidate_list),
                    "num_scored": len(scored),
                    "top_k": top_k,
                    "top_results": top_results,
                }
            )

            if expand_fn is None or stage_index == stages - 1:
                break

            expanded: list[Any] = []
            for result in top_results:
                additions = expand_fn(result["candidate"], result)
                if additions:
                    expanded.extend(additions)
            candidate_list = expanded

        evidence = [result.get("evidence", "") for result in top_results]
        if extract_prompt_fn is not None and top_results:
            extraction_prompts = [
                extract_prompt_fn(result["candidate"], result, query) for result in top_results
            ]
            evidence = self.adaptive_batch(
                extraction_prompts,
                model=model,
                batch_size=batch_size,
            )

        return {
            "query": query,
            "top_results": top_results,
            "evidence": evidence,
            "stages": stage_summaries,
            "stats": self.adaptive_stats(),
        }

    def adaptive_stats(self) -> dict[str, Any]:
        """Return a copy of adaptive scheduling metrics."""
        return {
            **self.metrics,
            "topologies": list(self.metrics["topologies"]),
            "wave_sizes": list(self.metrics["wave_sizes"]),
        }

    def normalize_batch_size(self, batch_size: int | None) -> int:
        if batch_size is None:
            return self.max_batch_size
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        return min(batch_size, self.max_batch_size)

    def get_query_fn(self, query: str) -> QueryFn:
        if query == "llm":
            return self.llm_query_batched
        if query == "rlm":
            return self.rlm_query_batched
        raise ValueError("query must be 'llm' or 'rlm'")

    def record_topology(self, name: str) -> None:
        topologies: list[str] = self.metrics["topologies"]
        if name not in topologies:
            topologies.append(name)

    @staticmethod
    def render_node_prompt(node: dict[str, Any], answers: dict[str, str]) -> str:
        if "prompt" in node:
            return str(node["prompt"])
        if "prompt_template" in node:
            return str(node["prompt_template"]).format(**answers)
        raise ValueError(f"DAG node {node.get('id')!r} must define prompt or prompt_template")

    @staticmethod
    def normalize_search_result(
        parsed: dict[str, Any],
        raw_response: str,
        candidate: Any,
        index: int,
    ) -> dict[str, Any]:
        result = dict(parsed or {})
        try:
            score = float(result.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0
        result["score"] = max(0.0, min(1.0, score))
        result.setdefault("reason", "")
        result.setdefault("evidence", "")
        result["candidate"] = candidate
        result["candidate_index"] = index
        result["raw_response"] = raw_response
        return result
