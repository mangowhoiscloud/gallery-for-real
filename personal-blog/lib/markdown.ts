export function generateExcerpt(content: string, maxLength: number = 150): string {
  const text = content
    .replace(/```[\s\S]*?```/g, '') // fenced code blocks
    .replace(/`[^`\n]+`/g, '') // inline code
    .replace(/^#{1,6}\s+/gm, '') // headings
    .replace(/!\[[^\]]*\]\([^)]+\)/g, '') // images
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links → text
    .replace(/[*_]{1,2}([^*_\n]+)[*_]{1,2}/g, '$1') // bold/italic
    .replace(/^>\s+/gm, '') // blockquotes
    .replace(/^[-*_]{3,}\s*$/gm, '') // horizontal rules
    .replace(/<[^>]+>/g, '') // HTML tags
    .replace(/\s+/g, ' ')
    .trim();

  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export interface Heading {
  id: string;
  text: string;
  level: number;
}

function headingToId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s가-힣]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export function extractHeadings(content: string): Heading[] {
  const headings: Heading[] = [];
  const lines = content.split('\n');
  let inCodeBlock = false;

  for (const line of lines) {
    if (line.startsWith('```')) {
      inCodeBlock = !inCodeBlock;
      continue;
    }
    if (inCodeBlock) continue;

    const match = line.match(/^(#{2,3})\s+(.+)$/);
    if (match) {
      const level = match[1].length;
      const text = match[2].trim();
      headings.push({ id: headingToId(text), text, level });
    }
  }

  return headings;
}

export function calculateReadingTime(content: string): string {
  const CHARS_PER_MIN = 500;
  const text = content
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`[^`\n]+`/g, '')
    .replace(/[*_#[\]()>]/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  const minutes = Math.ceil(text.length / CHARS_PER_MIN);
  return `${minutes}분 소요`;
}
