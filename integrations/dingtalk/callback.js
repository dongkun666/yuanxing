const crypto = require('crypto');
const config = require('./config');
const {getUserInfoByCode, getUserDetail} = require('./auth');

function verifySignature(signature, timestamp, nonce, token) {
  const arr = [token, timestamp, nonce].sort();
  const sha1 = crypto.createHash('sha1');
  sha1.update(arr.join(''));
  const hash = sha1.digest('hex');
  return hash === signature;
}

function decryptMessage(encryptedMsg, signature, timestamp, nonce, aesKey) {
  try {
    const key = Buffer.from(aesKey + '=', 'base64');
    const iv = key.slice(0, 16);

    const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
    decipher.setAutoPadding(false);

    let decrypted = decipher.update(encryptedMsg, 'base64', 'utf8');
    decrypted += decipher.final('utf8');

    const pad = decrypted.charCodeAt(decrypted.length - 1);
    decrypted = decrypted.slice(0, -pad);

    return decrypted;
  } catch (error) {
    console.error('解密钉钉消息失败:', error.message);
    throw error;
  }
}

function encryptMessage(content, aesKey, corpId) {
  try {
    const key = Buffer.from(aesKey + '=', 'base64');
    const iv = key.slice(0, 16);

    const randomStr = crypto.randomBytes(16).toString('binary');
    const contentBuf = Buffer.from(content, 'utf8');
    const corpIdBuf = Buffer.from(corpId, 'utf8');

    const msgLen = Buffer.alloc(4);
    msgLen.writeUInt32BE(contentBuf.length, 0);

    const fullContent = Buffer.concat([
      Buffer.from(randomStr, 'binary'),
      msgLen,
      contentBuf,
      corpIdBuf,
    ]);

    const blockSize = 32;
    const pad = blockSize - (fullContent.length % blockSize);
    const paddedContent = Buffer.concat([
      fullContent,
      Buffer.alloc(pad, pad),
    ]);

    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    cipher.setAutoPadding(false);
    let encrypted = cipher.update(paddedContent, null, 'base64');
    encrypted += cipher.final('base64');

    return encrypted;
  } catch (error) {
    console.error('加密钉钉消息失败:', error.message);
    throw error;
  }
}

async function handleOAuthCallback(authCode, state = '') {
  try {
    const userInfo = await getUserInfoByCode(authCode);
    const userDetail = await getUserDetail(userInfo.userId);

    return {
      success: true,
      userId: userInfo.userId,
      user: userDetail,
      state: state,
    };
  } catch (error) {
    console.error('处理钉钉 OAuth 回调错误:', error.message);
    throw error;
  }
}

function handleEventCallback(eventData) {
  const eventType = eventData.EventType;

  switch (eventType) {
    case 'user_add_org':
      return handleUserAdd(eventData);
    case 'user_modify_org':
      return handleUserModify(eventData);
    case 'user_leave_org':
      return handleUserLeave(eventData);
    case 'org_dept_create':
      return handleDeptCreate(eventData);
    case 'org_dept_modify':
      return handleDeptModify(eventData);
    case 'org_dept_remove':
      return handleDeptRemove(eventData);
    case 'bpms_task_change':
      return handleApprovalTaskChange(eventData);
    case 'bpms_instance_change':
      return handleApprovalInstanceChange(eventData);
    default:
      console.log('未处理的事件类型:', eventType);
      return {success: true};
  }
}

function handleUserAdd(eventData) {
  console.log('新增用户:', eventData.userId);
  return {success: true};
}

function handleUserModify(eventData) {
  console.log('更新用户:', eventData.userId);
  return {success: true};
}

function handleUserLeave(eventData) {
  console.log('离职用户:', eventData.userId);
  return {success: true};
}

function handleDeptCreate(eventData) {
  console.log('新增部门:', eventData.deptId);
  return {success: true};
}

function handleDeptModify(eventData) {
  console.log('更新部门:', eventData.deptId);
  return {success: true};
}

function handleDeptRemove(eventData) {
  console.log('删除部门:', eventData.deptId);
  return {success: true};
}

function handleApprovalTaskChange(eventData) {
  console.log('审批任务变更:', eventData.processInstanceId);
  return {success: true};
}

function handleApprovalInstanceChange(eventData) {
  console.log('审批实例变更:', eventData.processInstanceId);
  return {success: true};
}

module.exports = {
  verifySignature,
  decryptMessage,
  encryptMessage,
  handleOAuthCallback,
  handleEventCallback,
};
