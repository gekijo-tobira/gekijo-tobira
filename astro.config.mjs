import fs from 'node:fs';
import path from 'node:path';
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const SITE = 'https://gekijo-tobira.com';
const ARTICLES_DIR = 'src/pages/articles';

// sitemap の lastmod は、記事ファイルの updatedISO をそのまま使う。
// ビルド時刻を入れると、CSSを直しただけのビルドでも全記事の更新日が動いてしまい、
// Google に「日付が当てにならないサイト」と判断されて lastmod を無視される。
// （CLAUDE.md ⑪「中身が変わっていないのに更新日だけ新しくするのは避ける」と同じ考え方）
// 記事の updatedISO を書き換えれば、ここは自動で追従する。
function articleLastmodMap() {
  const map = new Map();
  for (const file of fs.readdirSync(ARTICLES_DIR)) {
    if (!file.endsWith('.astro')) continue;
    const src = fs.readFileSync(path.join(ARTICLES_DIR, file), 'utf-8');
    const matched = src.match(/const updatedISO\s*=\s*'(\d{4}-\d{2}-\d{2})'/);
    if (!matched) continue;
    map.set(`${SITE}/articles/${file.replace(/\.astro$/, '')}/`, matched[1]);
  }
  return map;
}

const LASTMOD = articleLastmodMap();

export default defineConfig({
  site: SITE,
  output: 'static',
  // 本番（Cloudflare Pages）が末尾スラッシュありへ308リダイレクトするため always に合わせる
  trailingSlash: 'always',
  integrations: [
    sitemap({
      // 検索結果に出す必要のないページは除外する
      // contact … Googleフォームの埋め込みだけで、検索から来ても読むものがない
      filter: (page) => !page.includes('/contact-thanks') && !page.endsWith('/contact/'),
      changefreq: 'monthly',
      // 記事は updatedISO を lastmod にする。日付を持たないページには lastmod を出さない
      serialize(item) {
        const lastmod = LASTMOD.get(item.url);
        return lastmod ? { ...item, lastmod } : item;
      },
    }),
  ],
});
