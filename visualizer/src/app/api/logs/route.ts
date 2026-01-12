import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const logExtension = '.jsonl';

function getLogDirectories() {
  const appDir = process.cwd();
  return [
    path.resolve(appDir, '..', 'logs'),
    path.resolve(appDir, 'public', 'logs'),
  ];
}

function sanitizeFileName(fileName: string) {
  const baseName = path.basename(fileName);
  if (!baseName.endsWith(logExtension)) {
    return null;
  }
  return baseName;
}

async function listLogFiles() {
  const dirs = getLogDirectories();
  const results: string[] = [];

  for (const dir of dirs) {
    try {
      const entries = await fs.readdir(dir);
      for (const entry of entries) {
        if (entry.endsWith(logExtension) && !results.includes(entry)) {
          results.push(entry);
        }
      }
    } catch {
      continue;
    }
  }

  return results.sort().reverse();
}

async function readLogFile(fileName: string) {
  const safeName = sanitizeFileName(fileName);
  if (!safeName) {
    return null;
  }

  for (const dir of getLogDirectories()) {
    const filePath = path.join(dir, safeName);
    try {
      return await fs.readFile(filePath, 'utf-8');
    } catch {
      continue;
    }
  }

  return null;
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const fileName = searchParams.get('file');

  if (fileName) {
    const content = await readLogFile(fileName);
    if (content == null) {
      return NextResponse.json({ error: 'Log file not found' }, { status: 404 });
    }
    return new NextResponse(content, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    });
  }

  const files = await listLogFiles();
  return NextResponse.json({ files });
}
