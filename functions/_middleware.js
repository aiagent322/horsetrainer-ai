// Send *.pages.dev traffic (production + previews) to the canonical domain.
export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.hostname.endsWith('.pages.dev')) {
    return Response.redirect('https://horsetrainer.ai' + url.pathname + url.search, 301);
  }
  return context.next();
}
