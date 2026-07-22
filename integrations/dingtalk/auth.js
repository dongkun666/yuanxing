const axios = require('axios');
const crypto = require('crypto');
const config = require('./config');

let accessToken = null;
let tokenExpiry = 0;

async function getAccessToken() {
  const now = Date.now();
  if (accessToken && now < tokenExpiry) {
    return accessToken;
  }

  try {
    const response = await axios.get(`${config.baseUrl}/gettoken`, {
      params: {
        appkey: config.appKey,
        appsecret: config.appSecret,
      },
    });

    if (response.data.errcode === 0) {
      accessToken = response.data.access_token;
      tokenExpiry = now + (response.data.expires_in - 300) * 1000;
      return accessToken;
    } else {
      throw new Error(`获取钉钉 AccessToken 失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取钉钉 AccessToken 错误:', error.message);
    throw error;
  }
}

async function getUserInfoByCode(authCode) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/v2/user/getuserinfo`,
      {
        code: authCode,
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {
        userId: response.data.userid,
        name: response.data.name,
        mobile: response.data.mobile,
        avatar: response.data.avatar,
      };
    } else {
      throw new Error(`获取用户信息失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('钉钉获取用户信息错误:', error.message);
    throw error;
  }
}

async function getUserDetail(userId) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/v2/user/get`,
      {
        userid: userId,
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {
        userid: response.data.result.userid,
        name: response.data.result.name,
        mobile: response.data.result.mobile,
        email: response.data.result.email,
        avatar: response.data.result.avatar,
        dept_id_list: response.data.result.dept_id_list,
        title: response.data.result.title,
        job_number: response.data.result.job_number,
        work_place: response.data.result.work_place,
        remark: response.data.result.remark,
      };
    } else {
      throw new Error(`获取用户详情失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取用户详情错误:', error.message);
    throw error;
  }
}

async function getDepartmentList(deptId = 1) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/v2/department/listsub`,
      {
        dept_id: deptId,
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return response.data.result || [];
    } else {
      throw new Error(`获取部门列表失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取部门列表错误:', error.message);
    throw error;
  }
}

async function getDepartmentUserList(deptId, cursor = 0, size = 50) {
  try {
    const accessToken = await getAccessToken();
    const response = await axios.post(
      `${config.baseUrl}/topapi/v2/user/list`,
      {
        dept_id: deptId,
        cursor: cursor,
        size: size,
      },
      {
        params: {
          access_token: accessToken,
        },
      },
    );

    if (response.data.errcode === 0) {
      return {
        list: response.data.result.list || [],
        hasMore: response.data.result.has_more,
        nextCursor: response.data.result.next_cursor,
      };
    } else {
      throw new Error(`获取部门成员失败: ${response.data.errmsg}`);
    }
  } catch (error) {
    console.error('获取部门成员错误:', error.message);
    throw error;
  }
}

function generateOAuthUrl(state = '') {
  const baseUrl = 'https://login.dingtalk.com/oauth2/auth';
  const params = new URLSearchParams({
    redirect_uri: config.oauth.redirectUri,
    response_type: 'code',
    client_id: config.appKey,
    scope: 'openid',
    state: state,
    prompt: 'consent',
  });
  return `${baseUrl}?${params.toString()}`;
}

function generateSignature(timestamp, secret) {
  const stringToSign = timestamp + '\n' + secret;
  const hmac = crypto.createHmac('sha256', stringToSign);
  const signature = hmac.digest('base64');
  return encodeURIComponent(signature);
}

module.exports = {
  getAccessToken,
  getUserInfoByCode,
  getUserDetail,
  getDepartmentList,
  getDepartmentUserList,
  generateOAuthUrl,
  generateSignature,
};
