import type { PostMeta } from './types';

export interface ValidationResult {
  valid: PostMeta[];
  warnings: string[];
}

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function isValidISODate(date: string): boolean {
  if (!ISO_DATE_RE.test(date)) return false;
  const [year, month, day] = date.split('-').map(Number);
  const d = new Date(date);
  return (
    !isNaN(d.getTime()) &&
    d.getUTCFullYear() === year &&
    d.getUTCMonth() + 1 === month &&
    d.getUTCDate() === day
  );
}

export function validatePosts(posts: PostMeta[]): ValidationResult {
  const warnings: string[] = [];
  const slugsSeen = new Set<string>();
  const valid: PostMeta[] = [];

  for (const post of posts) {
    const missing: string[] = [];
    if (!post.title) missing.push('title');
    if (!post.date) missing.push('date');
    if (!post.slug) missing.push('slug');

    if (missing.length > 0) {
      warnings.push(
        `Post missing required fields: ${missing.join(', ')} (slug: ${post.slug ?? 'unknown'})`
      );
      continue;
    }

    if (!isValidISODate(post.date)) {
      warnings.push(
        `Post "${post.slug}" has invalid date format: "${post.date}" (expected YYYY-MM-DD)`
      );
      continue;
    }

    if (slugsSeen.has(post.slug)) {
      warnings.push(`Duplicate slug detected: "${post.slug}"`);
      continue;
    }

    slugsSeen.add(post.slug);
    valid.push(post);
  }

  return { valid, warnings };
}
