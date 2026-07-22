module.exports = {
  corpId: process.env.WECOM_CORP_ID || '',
  corpSecret: process.env.WECOM_CORP_SECRET || '',
  agentId: process.env.WECOM_AGENT_ID || '',
  
  token: process.env.WECOM_TOKEN || '',
  encodingAESKey: process.env.WECOM_ENCODING_AES_KEY || '',
  
  baseUrl: 'https://qyapi.weixin.qq.com',
  
  oauth: {
    redirectUri: process.env.WECOM_REDIRECT_URI || 'https://lexprime.com/api/gateway/wecom/callback',
    scope: 'snsapi_base',
  },
  
  webhook: {
    defaultBotKey: process.env.WECOM_BOT_KEY || '',
  },
  
  approval: {
    templateId: process.env.WECOM_APPROVAL_TEMPLATE_ID || '',
  },
};
