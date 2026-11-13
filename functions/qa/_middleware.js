const oldOrigin = 'https://horsetrainer-ai.pages.dev';
const publicOrigin = 'https://horsetrainer.ai';

export async function onRequest(context) {
  const response = await context.next();
  if (!response.headers.get('Content-Type')?.includes('text/html') || !response.body) return response;

  const rewrite = (selector, attribute) => ({
    element(element) {
      const value = element.getAttribute(attribute);
      if (value?.startsWith(oldOrigin + '/qa/')) {
        element.setAttribute(attribute, publicOrigin + value.slice(oldOrigin.length));
      }
    },
  });

  return new HTMLRewriter()
    .on('link[rel="canonical"]', rewrite('link', 'href'))
    .on('meta[property="og:url"]', rewrite('meta', 'content'))
    .transform(response);
}
