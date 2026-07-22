import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import {useDispatch, useSelector} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import ReactNativeBiometrics from 'react-native-biometrics';

import {COLORS, SIZES} from '../theme';
import {login, clearError} from '../store/slices/authSlice';

const LoginScreen = ({navigation}) => {
  const dispatch = useDispatch();
  const {loading, error} = useSelector(state => state.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);

  React.useEffect(() => {
    checkBiometric();
    return () => {
      dispatch(clearError());
    };
  }, []);

  const checkBiometric = async () => {
    try {
      const {available} = await ReactNativeBiometrics.isSensorAvailable();
      setBiometricAvailable(available);
    } catch (error) {
      console.log('生物识别不可用', error);
    }
  };

  const handleLogin = async () => {
    if (!agreeTerms) {
      return;
    }
    if (!email || !password) {
      return;
    }
    dispatch(login({email, password}));
  };

  const handleBiometricLogin = async () => {
    try {
      const {success} = await ReactNativeBiometrics.simplePrompt({
        promptMessage: '使用生物识别登录',
      });
      if (success) {
        console.log('生物识别成功');
      }
    } catch (error) {
      console.log('生物识别失败', error);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{flex: 1}}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}>
          <View style={styles.logoSection}>
            <Text style={styles.logoIcon}>⚖️</Text>
            <Text style={styles.appName}>LexPrime</Text>
            <Text style={styles.appSlogan}>智能法律助手</Text>
          </View>

          <View style={styles.formSection}>
            <View style={styles.inputGroup}>
              <View style={styles.inputWrapper}>
                <Icon
                  name="mail-outline"
                  size={22}
                  color={COLORS.light.textSecondary}
                />
                <TextInput
                  style={styles.input}
                  placeholder="邮箱地址"
                  placeholderTextColor={COLORS.light.textLight}
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <View style={styles.inputWrapper}>
                <Icon
                  name="lock-closed-outline"
                  size={22}
                  color={COLORS.light.textSecondary}
                />
                <TextInput
                  style={styles.input}
                  placeholder="密码"
                  placeholderTextColor={COLORS.light.textLight}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                />
                <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
                  <Icon
                    name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                    size={22}
                    color={COLORS.light.textSecondary}
                  />
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity style={styles.forgotPassword}>
              <Text style={styles.forgotText}>忘记密码？</Text>
            </TouchableOpacity>

            {error && <Text style={styles.errorText}>{error}</Text>}

            <TouchableOpacity
              style={[styles.loginBtn, loading && styles.loginBtnDisabled]}
              onPress={handleLogin}
              disabled={loading}>
              {loading ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.loginBtnText}>登录</Text>
              )}
            </TouchableOpacity>

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>或</Text>
              <View style={styles.dividerLine} />
            </View>

            {biometricAvailable && (
              <TouchableOpacity
                style={styles.biometricBtn}
                onPress={handleBiometricLogin}>
                <Icon
                  name="fingerprint"
                  size={28}
                  color={COLORS.light.primary}
                />
                <Text style={styles.biometricText}>生物识别登录</Text>
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.termsSection}>
            <TouchableOpacity
              style={styles.checkboxRow}
              onPress={() => setAgreeTerms(!agreeTerms)}>
              <View style={[styles.checkbox, agreeTerms && styles.checkboxChecked]}>
                {agreeTerms && <Icon name="checkmark" size={14} color="#fff" />}
              </View>
              <Text style={styles.termsText}>
                我已阅读并同意
                <Text style={styles.termsLink}>《用户协议》</Text>
                和
                <Text style={styles.termsLink}>《隐私政策》</Text>
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.registerSection}>
            <Text style={styles.registerText}>还没有账号？</Text>
            <TouchableOpacity>
              <Text style={styles.registerLink}>立即注册</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: SIZES.padding,
    paddingTop: 60,
    paddingBottom: 40,
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 50,
  },
  logoIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  appName: {
    fontSize: 32,
    fontWeight: '700',
    color: COLORS.light.primary,
    marginBottom: 8,
  },
  appSlogan: {
    fontSize: 16,
    color: COLORS.light.textSecondary,
  },
  formSection: {
    marginBottom: 32,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.light.background,
    borderRadius: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  input: {
    flex: 1,
    height: 52,
    fontSize: 15,
    color: COLORS.light.text,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotText: {
    fontSize: 14,
    color: COLORS.light.primary,
  },
  errorText: {
    color: COLORS.light.danger,
    fontSize: 13,
    marginBottom: 12,
    textAlign: 'center',
  },
  loginBtn: {
    backgroundColor: COLORS.light.primary,
    borderRadius: 12,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loginBtnDisabled: {
    opacity: 0.6,
  },
  loginBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 28,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: COLORS.light.border,
  },
  dividerText: {
    paddingHorizontal: 20,
    fontSize: 14,
    color: COLORS.light.textLight,
  },
  biometricBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    borderWidth: 1,
    borderColor: COLORS.light.border,
    borderRadius: 12,
    height: 54,
  },
  biometricText: {
    fontSize: 15,
    color: COLORS.light.primary,
    fontWeight: '500',
  },
  termsSection: {
    marginBottom: 32,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: COLORS.light.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  checkboxChecked: {
    backgroundColor: COLORS.light.primary,
    borderColor: COLORS.light.primary,
  },
  termsText: {
    flex: 1,
    fontSize: 13,
    color: COLORS.light.textSecondary,
    lineHeight: 20,
  },
  termsLink: {
    color: COLORS.light.primary,
  },
  registerSection: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
  },
  registerText: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
  },
  registerLink: {
    fontSize: 14,
    color: COLORS.light.primary,
    fontWeight: '500',
  },
});

export default LoginScreen;
