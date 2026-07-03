const axios = require('axios');
const config = require('./config');
const {getAccessToken} = require('./auth');

async function sendTextMessage(userId, content) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/cgi-bin/message/send?access_token=${accessToken}`,
      {
        touser: userId,
        msgtype: 'text',
        agentid: config.agentId,
        text: {
          content: content,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {success: true, messageId: response.data.msgid};
    } else {
      throw new Error(`发送文本消息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送企业微信文本消息错误:', error.message);
    throw error;
  }
}

async function sendMarkdownMessage(userId, content) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/cgi-bin/message/send?access_token=${accessToken}`,
      {
        touser: userId,
        msgtype: 'markdown',
        agentid: config.agentId,
        markdown: {
          content: content,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {success: true, messageId: response.data.msgid};
    } else {
      throw new Error(`发送 Markdown 消息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送企业微信 Markdown 消息错误:', error.message);
    throw error;
  }
}

async function sendCardMessage(userId, cardData) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/cgi-bin/message/send?access_token=${accessToken}`,
      {
        touser: userId,
        msgtype: 'textcard',
        agentid: config.agentId,
        textcard: {
          title: cardData.title,
          description: cardData.description,
          url: cardData.url,
          btntxt: cardData.btnText || '详情',
        },
      },
    );

    if (response.data.errcode === 0) {
      return {success: true, messageId: response.data.msgid};
    } else {
      throw new Error(`发送卡片消息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('发送企业微信卡片消息错误:', error.message);
    throw error;
  }
}

async function sendWebhookMessage(webhookKey, content, msgType = 'text') {
  try {
    const url = `${config.baseUrl}/cgi-bin/webhook/send?key=${webhookKey}`;
    let payload;

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
            content: content,
          },
        };
        break;
      case 'news':
        payload = {
          msgtype: 'news',
          news: {
            articles: content,
          },
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
    console.error('发送企业微信群机器人消息错误:', error.message);
    throw error;
  }
}

async function sendContractReviewNotification(userId, reviewData) {
  const content = `
**合同审查完成通知**

> 合同类型：${reviewData.contractType || '未知'}
> 风险评分：${reviewData.riskScore || 0} 分
> 发现风险：${reviewData.riskCount || 0} 项

请及时查看审查结果，点击下方链接查看详情。
  `.trim();

  return sendMarkdownMessage(userId, content);
}

async function sendCaseUpdateNotification(userId, caseData) {
  const content = `
**案件更新通知**

> 案件名称：${caseData.caseName || '未知案件'}
> 更新时间：${caseData.updateTime || new Date().toLocaleString()}
> 更新内容：${caseData.updateContent || '有新的进展'}

点击查看详情
  `.trim();

  return sendMarkdownMessage(userId, content);
}

async function sendScheduleReminder(userId, scheduleData) {
  const content = `
**日程提醒**

> 日程：${scheduleData.title || '未命名日程'}
> 时间：${scheduleData.date} ${scheduleData.time || '全天'}
> 类型：${scheduleData.typeName || '其他'}
${scheduleData.location ? `> 地点：${scheduleData.location}` : ''}

请准时参加。
  `.trim();

  return sendMarkdownMessage(userId, content);
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
