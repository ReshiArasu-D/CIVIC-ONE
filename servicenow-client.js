/**
 * ServiceNow REST API Client for CIVIC-ONE (Node.js)
 * Uses native fetch (Node 18+) with zero external dependencies.
 */

const fs = require('fs');
const path = require('path');

function loadEnv(filePath) {
  const envPath = filePath || path.resolve(__dirname, '.env');
  if (!fs.existsSync(envPath)) return;
  const content = fs.readFileSync(envPath, 'utf-8');
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) continue;
    const [key, ...rest] = trimmed.split('=');
    const val = rest.join('=').trim().replace(/^['"]|['"]$/g, '');
    if (key && !process.env[key.trim()]) {
      process.env[key.trim()] = val;
    }
  }
}

class ServiceNowClient {
  constructor({ instanceUrl, username, password } = {}) {
    loadEnv();
    this.instanceUrl = (instanceUrl || process.env.SERVICENOW_INSTANCE_URL || '').replace(/\/+$/, '');
    this.username = username || process.env.SERVICENOW_USERNAME || '';
    this.password = password || process.env.SERVICENOW_PASSWORD || '';

    if (!this.instanceUrl || !this.username || !this.password) {
      throw new Error(
        'Missing ServiceNow credentials. Check SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD in .env'
      );
    }

    const token = Buffer.from(`${this.username}:${this.password}`).toString('base64');
    this.authHeader = `Basic ${token}`;
  }

  async _request(method, endpoint, { params, body } = {}) {
    let url = `${this.instanceUrl}/${endpoint.replace(/^\/+/, '')}`;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const options = {
      method,
      headers: {
        Authorization: this.authHeader,
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const res = await fetch(url, options);
    if (!res.ok) {
      const text = await res.text();
      let errorMsg = text;
      try {
        const json = JSON.parse(text);
        errorMsg = json.error?.message || json.error?.detail || text;
      } catch (_) {}
      throw new Error(`ServiceNow API Error (${res.status}): ${errorMsg}`);
    }

    if (res.status === 204) return null;
    return await res.json();
  }

  async testConnection() {
    const userRes = await this._request('GET', '/api/now/table/sys_user', {
      params: {
        sysparm_query: `user_name=${this.username}`,
        sysparm_fields: 'sys_id,user_name,name,email,active',
        sysparm_limit: '1',
      },
    });

    const user = userRes?.result?.[0] || null;

    const props = await this._request('GET', '/api/now/table/sys_properties', {
      params: {
        sysparm_query: 'name=glide.war',
        sysparm_fields: 'value',
        sysparm_limit: '1',
      },
    });
    const buildVersion = props?.result?.[0]?.value || 'Unknown';

    return {
      connected: true,
      instanceUrl: this.instanceUrl,
      user,
      buildVersion,
    };
  }

  async getRecords(table, { query = '', fields = '', limit = 10, offset = 0 } = {}) {
    const params = { sysparm_limit: String(limit), sysparm_offset: String(offset) };
    if (query) params.sysparm_query = query;
    if (fields) params.sysparm_fields = fields;

    const data = await this._request('GET', `/api/now/table/${table}`, { params });
    return data.result || [];
  }

  async getRecord(table, sysId, { fields = '' } = {}) {
    const params = {};
    if (fields) params.sysparm_fields = fields;
    const data = await this._request('GET', `/api/now/table/${table}/${sysId}`, { params });
    return data.result || null;
  }

  async createRecord(table, body) {
    const data = await this._request('POST', `/api/now/table/${table}`, { body });
    return data.result || null;
  }

  async updateRecord(table, sysId, body) {
    const data = await this._request('PATCH', `/api/now/table/${table}/${sysId}`, { body });
    return data.result || null;
  }

  async deleteRecord(table, sysId) {
    await this._request('DELETE', `/api/now/table/${table}/${sysId}`);
    return true;
  }
}

module.exports = { ServiceNowClient };

if (require.main === module) {
  (async () => {
    try {
      console.log('Testing connection to ServiceNow via Node.js...');
      const client = new ServiceNowClient();
      const info = await client.testConnection();
      console.log('==================================================');
      console.log('SUCCESS: Connected to ServiceNow!');
      console.log(`Instance URL: ${info.instanceUrl}`);
      console.log(`Logged in User: ${info.user?.name} (${info.user?.user_name})`);
      console.log(`User Email: ${info.user?.email}`);
      console.log(`ServiceNow Build: ${info.buildVersion}`);
      console.log('==================================================');
    } catch (err) {
      console.error('Connection failed:', err.message);
      process.exit(1);
    }
  })();
}
