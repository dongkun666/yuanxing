const axios = require('axios');
const config = require('./config');

let accessToken = null;
let tokenExpiry = 0;

async function getAccessToken() {
  const now = Date.now();
  if (accessToken && now < tokenExpiry) {
    return accessToken;
  }

  try {
    const response = await axios.get(`${config.baseUrl}/cgi-bin/gettoken`, {
      params: {
        corpid: config.corpId,
        corpsecret: config.corpSecret,
      },
    });

    if (response.data.errcode === 0) {
      accessToken = response.data.access_token;
      tokenExpiry = now + (response.data.expires_in - 300) * 1000;
      return accessToken;
    } else {
      throw new Error(`获取企业微信 AccessToken 失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取企业微信 AccessToken 错误:', error.message);
    throw error;
  }
}

async function getUserIdByCode(code) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.get(`${config.baseUrl}/cgi-bin/user/getuserinfo`, {
      params: {
        access_token: accessToken,
        code: code,
      },
    });

    if (response.data.errcode === 0) {
      return {
        userId: response.data.UserId,
        deviceId: response.data.DeviceId,
      };
    } else {
      throw new Error(`获取用户信息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('企业微信 OAuth 错误:', error.message);
    throw error;
  }
}

async function getUserDetail(userId) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.get(`${config.baseUrl}/cgi-bin/user/get`, {
      params: {
        access_token: accessToken,
        userid: userId,
      },
    });

    if (response.data.errcode === 0) {
      return {
        userid: response.data.userid,
        name: response.data.name,
        mobile: response.data.mobile,
        email: response.data.email,
        avatar: response.data.avatar,
        department: response.data.department,
        position: response.data.position,
        gender: response.data.gender,
        status: response.data.status,
        extattr: response.data.extattr,
      };
    } else {
      throw new Error(`获取用户详情失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取用户详情错误:', error.message);
    throw error;
  }
}

async function getDepartmentList(departmentId = '') {
  try {
    const accessToken = await getAccessToken();
    const params = {access_token: accessToken};
    if (departmentId) {
      params.id = departmentId;
    }
    const response = await axios.get(`${config.baseUrl}/cgi-bin/department/list`, {
      params,
    });

    if (response.data.errcode === 0) {
      return response.data.department || [];
    } else {
      throw new Error(`获取部门列表失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取部门列表错误:', error.message);
    throw error;
  }
}

async function getDepartmentUserList(departmentId, fetchChild = true) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.get(`${config.baseUrl}/cgi-bin/user/list`, {
      params: {
        access_token: accessToken,
        department_id: departmentId,
        fetch_child: fetchChild ? 1 : 0,
      },
    });

    if (response.data.errcode === 0) {
      return response.data.userlist || [];
    } else {
      throw new Error(`获取部门成员失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取部门成员错误:', error.message);
    throw error;
  }
}

function generateOAuthUrl(state = '') {
  const baseUrl = 'https://open.weixin.qq.com/connect/oauth2/authorize';
  const params = new URLSearchParams({
    appid: config.corpId,
    redirect_uri: config.oauth.redirectUri,
    response_type: 'code',
    scope: config.oauth.scope,
    state: state,
  });
  return `${baseUrl}?${params.toString()}#wechat_redirect`;
}

module.exports = {
  getAccessToken,
  getUserIdByCode,
  getUserDetail,
  getDepartmentList,
  getDepartmentUserList,
  generateOAuthUrl,
};
