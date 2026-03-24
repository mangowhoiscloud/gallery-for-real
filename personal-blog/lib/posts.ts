import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import type { Post, PostMeta } from './types';

const POSTS_DIR = path.join(process.cwd(), 'content/posts');

export async function getAllPosts(postsDir: string = POSTS_DIR): Promise<PostMeta[]> {
  const filenames = await fs.promises.readdir(postsDir);
  const posts = await Promise.all(
    filenames
      .filter((f) => f.endsWith('.md'))
      .map(async (filename) => {
        const filePath = path.join(postsDir, filename);
        const fileContent = await fs.promises.readFile(filePath, 'utf-8');
        const { data } = matter(fileContent);
        return data as PostMeta;
      })
  );
  return posts.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
}

export async function getPostBySlug(
  slug: string,
  postsDir: string = POSTS_DIR
): Promise<Post | null> {
  const filenames = await fs.promises.readdir(postsDir);
  for (const filename of filenames) {
    if (!filename.endsWith('.md')) continue;
    const filePath = path.join(postsDir, filename);
    const fileContent = await fs.promises.readFile(filePath, 'utf-8');
    const { data, content } = matter(fileContent);
    if (data.slug === slug) {
      return { ...(data as PostMeta), content };
    }
  }
  return null;
}

export async function getPostSlugs(postsDir: string = POSTS_DIR): Promise<string[]> {
  const posts = await getAllPosts(postsDir);
  return posts.map((post) => post.slug);
}

export async function getCategories(
  postsDir: string = POSTS_DIR
): Promise<Record<string, number>> {
  const posts = await getAllPosts(postsDir);
  const counts: Record<string, number> = {};
  for (const post of posts) {
    counts[post.category] = (counts[post.category] ?? 0) + 1;
  }
  return counts;
}

export async function getAllTags(
  postsDir: string = POSTS_DIR
): Promise<Record<string, number>> {
  const posts = await getAllPosts(postsDir);
  const counts: Record<string, number> = {};
  for (const post of posts) {
    for (const tag of post.tags ?? []) {
      counts[tag] = (counts[tag] ?? 0) + 1;
    }
  }
  return counts;
}
