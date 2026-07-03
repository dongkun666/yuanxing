module.exports = {
  appKey: process.env.DINGTALK_APP_KEY || '',
  appSecret: process.env.DINGTALK_APP_SECRET || '',
  corpId: process.env.DINGTALK_CORP_ID || '',
  
  baseUrl: 'https://oapi.dingtalk.com',
  
  oauth: {
    redirectUri: process.env.DINGTALK_REDIRECT_URI || 'https://lexprime.com/api/gateway/dingtalk/callback',
  },
  
  webhook: {
    defaultAccessToken: process.env.DINGTALK_WEBHOOK_TOKEN || '',
    secret: process.env.DINGTALK_WEBHOOK_SECRET || '',
  },
  
  approval: {
    processCode: process.env.DINGTALK_APPROVAL_PROCESS_CODE || '',
  },
};
