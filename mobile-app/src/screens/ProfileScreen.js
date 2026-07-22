import React, {useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
} from 'react-native';
import {useSelector, useDispatch} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';

import {COLORS, SIZES, SHADOWS} from '../theme';
import {getCurrentUser, logout} from '../store/slices/authSlice';
import {gatewayApi} from '../api';
import {useState} from 'react';

const menuGroups = [
  {
    title: '我的服务',
    items: [
      {icon: 'star-outline', label: '我的收藏', page: 'favorites'},
      {icon: 'document-text-outline', label: '审查记录', page: 'review-history'},
      {icon: 'calendar-outline', label: '日程管理', page: 'schedule'},
      {icon: 'people-outline', label: '客户管理', page: 'clients'},
    ],
  },
  {
    title: '其他',
    items: [
      {icon: 'notifications-outline', label: '消息通知', page: 'notifications'},
      {icon: 'settings-outline', label: '设置', page: 'settings'},
      {icon: 'help-circle-outline', label: '帮助中心', page: 'help'},
      {icon: 'information-circle-outline', label: '关于我们', page: 'about'},
    ],
  },
];

const ProfileScreen = ({navigation}) => {
  const dispatch = useDispatch();
  const {user, isAuthenticated} = useSelector(state => state.auth);

  const [stats, setStats] = useState({
    favoriteCount: 0,
    reviewCount: 0,
    caseCount: 0,
  });

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(getCurrentUser());
      loadStats();
    }
  }, [isAuthenticated]);

  const loadStats = async () => {
    try {
      const res = await gatewayApi.getUserStats();
      if (res) {
        setStats(res);
      }
    } catch (error) {
      console.error('加载用户统计失败', error);
    }
  };

  const handleMenuPress = page => {
    if (!isAuthenticated) {
      navigation.navigate('Login');
      return;
    }
    console.log('导航到:', page);
  };

  const handleLogout = () => {
    dispatch(logout());
  };

  const handleLogin = () => {
    navigation.navigate('Login');
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.profileHeader}>
          <TouchableOpacity
            style={styles.userSection}
            onPress={isAuthenticated ? undefined : handleLogin}>
            {isAuthenticated && user?.avatar_url ? (
              <Image source={{uri: user.avatar_url}} style={styles.avatar} />
            ) : (
              <View style={styles.avatarPlaceholder}>
                <Icon name="person-outline" size={36} color="#fff" />
              </View>
            )}
            <View style={styles.userInfo}>
              <Text style={styles.userName}>
                {isAuthenticated
                  ? user?.name || user?.nickname || '用户'
                  : '点击登录'}
              </Text>
              <Text style={styles.userSubtitle}>
                {isAuthenticated ? user?.email || '' : '登录后享受更多功能'}
              </Text>
            </View>
            <Icon
              name="chevron-forward"
              size={24}
              color="rgba(255,255,255,0.6)"
            />
          </TouchableOpacity>

          {isAuthenticated && (
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{stats.favoriteCount}</Text>
                <Text style={styles.statLabel}>收藏</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{stats.reviewCount}</Text>
                <Text style={styles.statLabel}>审查</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statNumber}>{stats.caseCount}</Text>
                <Text style={styles.statLabel}>判例</Text>
              </View>
            </View>
          )}
        </View>

        {menuGroups.map((group, groupIndex) => (
          <View key={groupIndex} style={styles.menuSection}>
            <Text style={styles.groupTitle}>{group.title}</Text>
            <View style={styles.menuList}>
              {group.items.map((item, itemIndex) => (
                <TouchableOpacity
                  key={item.label}
                  style={[
                    styles.menuItem,
                    itemIndex < group.items.length - 1 && styles.menuItemBorder,
                  ]}
                  onPress={() => handleMenuPress(item.page)}>
                  <View style={styles.menuIcon}>
                    <Icon
                      name={item.icon}
                      size={22}
                      color={COLORS.light.primary}
                    />
                  </View>
                  <Text style={styles.menuLabel}>{item.label}</Text>
                  <Icon
                    name="chevron-forward"
                    size={18}
                    color={COLORS.light.textLight}
                  />
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        {isAuthenticated && (
          <View style={styles.logoutSection}>
            <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
              <Text style={styles.logoutText}>退出登录</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.version}>LexPrime v1.0.0</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.light.background,
  },
  profileHeader: {
    backgroundColor: COLORS.light.primary,
    paddingHorizontal: SIZES.padding,
    paddingTop: 40,
    paddingBottom: 30,
  },
  userSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  avatarPlaceholder: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 22,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
  },
  userSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginTop: 30,
    paddingTop: 24,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.2)',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  menuSection: {
    marginTop: 24,
    paddingHorizontal: SIZES.padding,
  },
  groupTitle: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
    marginBottom: 12,
    paddingLeft: 4,
  },
  menuList: {
    backgroundColor: '#fff',
    borderRadius: 16,
    overflow: 'hidden',
    ...SHADOWS.small,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
    gap: 14,
  },
  menuItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: COLORS.light.borderLight,
  },
  menuIcon: {
    width: 32,
    alignItems: 'center',
  },
  menuLabel: {
    flex: 1,
    fontSize: 15,
    color: COLORS.light.text,
  },
  logoutSection: {
    padding: SIZES.padding,
    marginTop: 8,
  },
  logoutBtn: {
    backgroundColor: '#fff',
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    ...SHADOWS.small,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.light.danger,
  },
  footer: {
    alignItems: 'center',
    paddingVertical: 30,
    paddingBottom: 50,
  },
  version: {
    fontSize: 12,
    color: COLORS.light.textLight,
  },
});

export default ProfileScreen;
