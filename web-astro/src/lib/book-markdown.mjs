const originalSite = 'https://bojieli.github.io/ai-agent-book';

// Adapt the web view only. The tracked book remains the shared PDF/website source.
export function bookMarkdown() {
  return (tree, file) => {
    const directory =
      file.path
        ?.replaceAll('\\', '/')
        .match(/\/(book(?:-en|-zhtw)?)\/chapter\d+(?:\.zhtw)?\.md$/)?.[1] ??
      'book-en';
    const suffix = directory === 'book-zhtw' ? '.zhtw' : '';
    if (tree.children[0]?.type === 'heading' && tree.children[0].depth === 1) {
      tree.children.shift();
    }
    const walk = (node) => {
      if (
        node.type === 'paragraph' &&
        node.children?.length === 1 &&
        node.children[0].type === 'image'
      ) {
        node.data = { ...node.data, hName: 'figure' };
        node.children.push({
          type: 'paragraph',
          data: { hName: 'figcaption' },
          children: [{ type: 'text', value: node.children[0].alt ?? '' }],
        });
      }
      if (node.type === 'image' && node.url.startsWith('images/')) {
        node.url = `/${directory}/${node.url}`;
      }
      if (
        node.type === 'link' &&
        !/^(?:[a-z][a-z\d+.-]*:|#|\/)/i.test(node.url)
      ) {
        if (/^chapter1(?:\.zhtw)?\.md(?:#|$)/.test(node.url)) {
          node.url = node.url.replace(
            /^chapter1(?:\.zhtw)?\.md/,
            `/${directory}/chapter1${suffix}/`,
          );
        } else {
          const resolved = new URL(node.url, `${originalSite}/${directory}/`);
          resolved.pathname = resolved.pathname.replace(/\.md$/, '/');
          node.url = resolved.href;
        }
      }
      // GFM treats Chinese list punctuation as URL text. Split bare autolinks only;
      // explicit Markdown links and their labels retain the author's intent.
      if (node.children)
        node.children = node.children.flatMap((child) => {
          const start = child.position?.start.offset;
          if (
            child.type !== 'link' ||
            child.children?.length !== 1 ||
            child.children[0].type !== 'text' ||
            child.children[0].value !== child.url ||
            !/、https?:\/\/|。$/.test(child.url) ||
            !String(file.value)
              .slice(start, start + 8)
              .match(/^https?:\/\//)
          )
            return [child];
          return child.url
            .split(/(、(?=https?:\/\/)|。$)/)
            .filter(Boolean)
            .map((part) =>
              /^https?:\/\//.test(part)
                ? {
                    ...child,
                    url: part,
                    children: [{ type: 'text', value: part }],
                  }
                : { type: 'text', value: part },
            );
        });
      node.children?.forEach(walk);
    };
    walk(tree);
  };
}

// Footnote UI is generated after Markdown parsing, so translate it in the HTML tree.
export function bookFootnotes() {
  return (tree, file) => {
    const path = file.path?.replaceAll('\\', '/') ?? '';
    const traditional = path.includes('/book-zhtw/');
    if (!traditional && !path.includes('/book/')) return;
    const walk = (node) => {
      if (node.type === 'element') {
        if (node.properties?.id === 'footnote-label') {
          node.children = [
            { type: 'text', value: traditional ? '註釋' : '注释' },
          ];
        }
        const label = node.properties?.ariaLabel;
        if (typeof label === 'string' && /^Back to reference /.test(label)) {
          node.properties.ariaLabel = label.replace(
            'Back to reference ',
            '返回引用 ',
          );
        }
      }
      node.children?.forEach(walk);
    };
    walk(tree);
  };
}
