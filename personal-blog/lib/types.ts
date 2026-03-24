export interface PostMeta {
  title: string;
  date: string;
  category: string;
  tags: string[];
  slug: string;
  original_url?: string;
}

export interface Post extends PostMeta {
  content: string;
}
