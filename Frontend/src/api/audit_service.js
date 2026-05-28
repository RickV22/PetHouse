import API_URL, { getAuthHeaders } from './api.js';

/**
 * Use real backend audit endpoints when available.
 */
function buildQuery(params = {}) {
	const esc = encodeURIComponent;
	return Object.keys(params)
		.filter((k) => params[k] !== undefined && params[k] !== null && params[k] !== '')
		.map((k) => `${esc(k)}=${esc(params[k])}`)
		.join('&');
}

export async function getAuditLogs(params = {}) {
	try {
		const headers = getAuthHeaders();

		const query = buildQuery(params);
		const url = `${API_URL}/audit-logs${query ? `?${query}` : ''}`;

		const res = await fetch(url, { headers });
		if (!res.ok) {
			const err = await res.text().catch(() => '');
			throw new Error(`Audit logs fetch failed: ${res.status} ${err}`);
		}

		const logs = await res.json();
		return Array.isArray(logs) ? logs : [];
	} catch (error) {
		console.error('getAuditLogs:', error);
		return [];
	}
}

export async function exportAuditLogsCSV(params = {}) {
	try {
		const headers = getAuthHeaders();
		const query = buildQuery(params);
		const url = `${API_URL}/audit-logs/export/csv${query ? `?${query}` : ''}`;

		const res = await fetch(url, { headers });
		if (!res.ok) throw new Error('Export failed');

		const data = await res.json();
		return data;
	} catch (error) {
		console.error('exportAuditLogsCSV:', error);
		throw error;
	}
}