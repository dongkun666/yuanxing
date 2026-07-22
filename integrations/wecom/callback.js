const crypto = require('crypto');
const config = require('./config');
const {getUserIdByCode, getUserDetail} = require('./auth');

function verifySignature(signature, timestamp, nonce, echostr) {
  const token = config.token;
  const arr = [token, timestamp, nonce, echostr].sort();
  const sha1 = crypto.createHash('sha1');
  sha1.update(arr.join(''));
  const hash = sha1.digest('hex');
  return hash === signature;
}

function decryptMessage(encryptedMsg, msgSignature, timestamp, nonce) {
  try {
    const encodingAESKey = config.encodingAESKey;
    const aesKey = Buffer.from(encodingAESKey + '=', 'base64');
    const iv = aesKey.slice(0, 16);

    const decipher = crypto.createDecipheriv('aes-256-cbc', aesKey, iv);
    decipher.setAutoPadding(false);

    let decrypted = decipher.update(encryptedMsg, 'base64', 'utf8');
    decrypted += decipher.final('utf8');

    const pad = decrypted.charCodeAt(decrypted.length - 1);
    decrypted = decrypted.slice(0, -pad);

    const content = decrypted.slice(16);
    const msgLen = content
      .slice(0, 4)
      .split('')
      .reduce((acc, char) => (acc << 8) + char.charCodeAt(0), 0);

    const xmlContent = content.slice(4, 4 + msgLen);
    const receiveId = content.slice(4 + msgLen);

    return {
      xml: xmlContent,
      receiveId: receiveId,
    };
  } catch (error) {
    console.error('解密企业微信消息失败:', error.message);
    throw error;
  }
}

function encryptMessage(xmlContent) {
  try {
    const encodingAESKey = config.encodingAESKey;
    const aesKey = Buffer.from(encodingAESKey + '=', 'base64');
    const iv = aesKey.slice(0, 16);

    const randomStr = crypto.randomBytes(16).toString('binary');
    const contentBytes = Buffer.from(xmlContent, 'utf8');
    const msgLen = Buffer.alloc(4);
    msgLen.writeUInt32BE(contentBytes.length, 0);
    const receiveId = Buffer.from(config.corpId, 'utf8');

    const fullContent = Buffer.concat([
      Buffer.from(randomStr, 'binary'),
      msgLen,
      contentBytes,
      receiveId,
    ]);

    const blockSize = 32;
    const pad = blockSize - (fullContent.length % blockSize);
    const paddedContent = Buffer.concat([
      fullContent,
      Buffer.alloc(pad, pad),
    ]);

    const cipher = crypto.createCipheriv('aes-256-cbc', aesKey, iv);
    cipher.setAutoPadding(false);
    let encrypted = cipher.update(paddedContent, null, 'base64');
    encrypted += cipher.final('base64');

    return encrypted;
  } catch (error) {
    console.error('加密企业微信消息失败:', error.message);
    throw error;
  }
}

function generateSignature(timestamp, nonce, encrypt) {
  const token = config.token;
  const arr = [token, timestamp, nonce, encrypt].sort();
  const sha1 = crypto.createHash('sha1');
  sha1.update(arr.join(''));
  return sha1.digest('hex');
}

async function handleOAuthCallback(code, state = '') {
  try {
    const {userId} = await getUserIdByCode(code);
    const userDetail = await getUserDetail(userId);

    return {
      success: true,
      userId: userId,
      user: userDetail,
      state: state,
    };
  } catch (error) {
    console.error('处理企业微信 OAuth 回调错误:', error.message);
    throw error;
  }
}

function handleEventCallback(xmlData) {
  const eventData = parseXml(xmlData);

  switch (eventData.Event) {
    case 'change_contact':
      return handleContactChange(eventData);
    case 'click':
      return handleMenuClick(eventData);
    case 'view':
      return handleMenuView(eventData);
    case 'location':
      return handleLocationReport(eventData);
    default:
      console.log('未处理的事件类型:', eventData.Event);
      return {success: true};
  }
}

function handleContactChange(eventData) {
  const changeType = eventData.ChangeType;

  switch (changeType) {
    case 'create_user':
      console.log('新增用户:', eventData.UserID);
      break;
    case 'update_user':
      console.log('更新用户:', eventData.UserID);
      break;
    case 'delete_user':
      console.log('删除用户:', eventData.UserID);
      break;
    case 'create_party':
      console.log('新增部门:', eventData.Id);
      break;
    case 'update_party':
      console.log('更新部门:', eventData.Id);
      break;
    case 'delete_party':
      console.log('删除部门:', eventData.Id);
      break;
    default:
      console.log('未处理的通讯录变更类型:', changeType);
  }

  return {success: true};
}

function handleMenuClick(eventData) {
  console.log('菜单点击事件:', eventData.EventKey);
  return {success: true};
}

function handleMenuView(eventData) {
  console.log('菜单跳转事件:', eventData.EventKey);
  return {success: true};
}

function handleLocationReport(eventData) {
  console.log('位置上报:', eventData.Latitude, eventData.Longitude);
  return {success: true};
}

function parseXml(xml) {
  const result = {};
  const regex = /<(\w+)>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/\1>/g;
  let match;
  while ((match = regex.exec(xml)) !== null) {
    result[match[1]] = match[2];
  }
  return result;
}

module.exports = {
  verifySignature,
  decryptMessage,
  encryptMessage,
  generateSignature,
  handleOAuthCallback,
  handleEventCallback,
};
