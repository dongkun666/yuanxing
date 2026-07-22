const axios = require('axios');
const crypto = require('crypto');
const config = require('./config');
const {getAccessToken, generateSignature} = require('./auth');

async function sendTextMessage(userId, content) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/message/corpconversation/asyncsend_v2`,
      {
        agent_id: config.agentId,
        userid_list: userId,
        msg: {
          msgtype: 'text',
          text: {
            content: content,
          },
        },
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {success: true, taskId: response.data.task_id};
    } else {
      throw new Error(`发送工作通知失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送钉钉工作通知错误:', error.message);
    throw error;
  }
}

async function sendMarkdownMessage(userId, title, text) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/message/corpconversation/asyncsend_v2`,
      {
        agent_id: config.agentId,
        userid_list: userId,
        msg: {
          msgtype: 'markdown',
          markdown: {
            title: title,
            text: text,
          },
        },
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {success: true, taskId: response.data.task_id};
    } else {
      throw new Error(`发送 Markdown 消息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送钉钉 Markdown 消息错误:', error.message);
    throw error;
  }
}

async function sendCardMessage(userId, cardData) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/message/corpconversation/asyncsend_v2`,
      {
        agent_id: config.agentId,
        userid_list: userId,
        msg: {
          msgtype: 'action_card',
          action_card: {
            title: cardData.title,
            markdown: cardData.markdown,
            single_title: cardData.btnTitle || '查看详情',
            single_url: cardData.url,
          },
        },
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {success: true, taskId: response.data.task_id};
    } else {
      throw new Error(`发送卡片消息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送钉钉卡片消息错误:', error.message);
    throw error;
  }
}

async function sendWebhookMessage(webhookUrl, content, msgType = 'text', secret = '') {
  try {
    let url = webhookUrl;
    let payload;

    if (secret) {
      const timestamp = Date.now();
      const sign = generateDingTalkSignature(timestamp, secret);
      url += `&timestamp=${timestamp}&sign=${sign}`;
    }

    switch (msgType) {
      case 'text':
        payload = {
          msgtype: 'text',
          text: {
            content: content,
          },
        };
        break;
      case 'markdown':
        payload = {
          msgtype: 'markdown',
          markdown: {
            title: content.title,
            text: content.text,
          },
        };
        break;
      case 'actionCard':
        payload = {
          msgtype: 'actionCard',
          actionCard: content,
        };
        break;
      default:
        throw new Error(`不支持的消息类型: ${msgType}`);
    }

    const response = await axios.post(url, payload);

    if (response.data.errcode === 0) {
      return {success: true};
    } else {
      throw new Error(`发送群机器人消息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送钉钉群机器人消息错误:', error.message);
    throw error;
  }
}

function generateDingTalkSignature(timestamp, secret) {
  const stringToSign = `${timestamp}\n${secret}`;
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(stringToSign);
  const signature = hmac.digest('base64');
  return encodeURIComponent(signature);
}

async function sendContractReviewNotification(userId, reviewData) {
  const title = '合同审查完成通知';
  const text = `
# 合同审查完成

> **合同类型**：${reviewData.contractType || '未知'}
> **风险评分**：${reviewData.riskScore || 0} 分
> **发现风险**：${reviewData.riskCount || 0} 项

请及时查看审查结果。

[点击查看详情](${reviewData.detailUrl || ''})
  `.trim();

  return sendMarkdownMessage(userId, title, text);
}

async function sendCaseUpdateNotification(userId, caseData) {
  const title = '案件更新通知';
  const text = `
# 案件更新

> **案件名称**：${caseData.caseName || '未知案件'}
> **更新时间**：${caseData.updateTime || new Date().toLocaleString()}
> **更新内容**：${caseData.updateContent || '有新的进展'}

点击查看详情
  `.trim();

  return sendMarkdownMessage(userId, title, text);
}

async function sendScheduleReminder(userId, scheduleData) {
  const title = '日程提醒';
  const text = `
# 日程提醒

> **日程**：${scheduleData.title || '未命名日程'}
> **时间**：${scheduleData.date} ${scheduleData.time || '全天'}
> **类型**：${scheduleData.typeName || '其他'}
${scheduleData.location ? `> **地点**：${scheduleData.location}` : ''}

请准时参加。
  `.trim();

  return sendMarkdownMessage(userId, title, text);
}

module.exports = {
  sendTextMessage,
  sendMarkdownMessage,
  sendCardMessage,
  sendWebhookMessage,
  sendContractReviewNotification,
  sendCaseUpdateNotification,
  sendScheduleReminder,
};
