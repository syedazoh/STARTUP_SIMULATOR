import { backendResponse } from '../../../../lib/backend';
export const dynamic = 'force-dynamic';
export async function GET(request: Request, {params}: {params: Promise<{businessId: string}>}) {
  const {businessId} = await params;
  const query = new URL(request.url).searchParams;
  const format = query.get('format') === 'csv' ? 'csv' : 'json';
  try {
    const response = await backendResponse(`/api/businesses/${encodeURIComponent(businessId)}/evidence?format=${format}`);
    return new Response(await response.text(), {headers: {
      'Content-Type': format === 'csv' ? 'text/csv; charset=utf-8' : 'application/json',
      'Content-Disposition': `attachment; filename="simulator-evidence.${format}"`,
      'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff',
      'X-Export-Truncated': response.headers.get('X-Export-Truncated') || 'false',
    }});
  } catch {
    return Response.json({error: 'Export unavailable. Sign in and verify access to this business, then retry.'}, {status: 503, headers: {'Cache-Control': 'private, no-store'}});
  }
}
