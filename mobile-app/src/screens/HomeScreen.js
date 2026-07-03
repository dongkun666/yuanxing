import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  FlatList,
  Image,
  ActivityIndicator,
} from 'react-native';
import {useSelector, useDispatch} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';

import {COLORS, SIZES, FONTS, SHADOWS} from '../theme';
import {fetchTodaySchedule} from '../store/slices/scheduleSlice';
import {casesApi, gatewayApi} from '../api';

const HomeScreen = ({navigation}) => {
  const dispatch = useDispatch();
  const {user, isAuthenticated} = useSelector(state => state.auth);
  const {todayList, todayLoading} = useSelector(state => state.schedule);

  const [searchKeyword, setSearchKeyword] = useState('');
  const [hotCases, setHotCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalCases: 0,
    todaySchedule: 0,
    pendingReview: 0,
  });

  useEffect(() => {
    loadData();
    if (isAuthenticated) {
      dispatch(fetchTodaySchedule());
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [casesRes, statsRes] = await Promise.all([
        casesApi.getCases({limit: 5}),
        gatewayApi.getStats(),
      ]);
      setHotCases(casesRes || []);
      setStats(statsRes || stats);
    } catch (error) {
      console.error('加载首页数据失败', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchKeyword.trim()) {
      navigation.navigate('Cases', {
        screen: 'CasesList',
        params: {keyword: searchKeyword},
      });
    }
  };

  const handleCasePress = docId => {
    navigation.navigate('CaseDetail', {docId});
  };

  const handleQuickAction = action => {
    switch (action) {
      case 'case-search':
        navigation.navigate('Cases', {screen: 'CasesList'});
        break;
      case 'contract-review':
        navigation.navigate('Contract', {screen: 'ContractReviewMain'});
        break;
      case 'schedule':
        navigation.navigate('Schedule');
        break;
      case 'ai-chat':
        navigation.navigate('AIChat');
        break;
    }
  };

  const quickActions = [
    {id: 1, icon: 'book-outline', label: '判例检索', action: 'case-search', color: '#3b82f6'},
    {id: 2, icon: 'document-text-outline', label: '合同审查', action: 'contract-review', color: '#10b981'},
    {id: 3, icon: 'calendar-outline', label: '日程管理', action: 'schedule', color: '#f59e0b'},
    {id: 4, icon: 'chatbubble-ellipses-outline', label: 'AI 咨询', action: 'ai-chat', color: '#8b5cf6'},
  ];

  const renderCaseItem = ({item}) => (
    <TouchableOpacity
      style={styles.caseCard}
      onPress={() => handleCasePress(item.doc_id)}
      activeOpacity={0.7}>
      <View style={styles.caseHeader}>
        <Text style={styles.caseName} numberOfLines={2}>
          {item.case_name}
        </Text>
        <View style={styles.causeBadge}>
          <Text style={styles.causeText}>{item.cause_category || '其他'}</Text>
        </View>
      </View>
      <View style={styles.caseInfo}>
        <Text style={styles.courtText}>{item.court}</Text>
        <Text style={styles.dateText}>{item.judgment_date}</Text>
      </View>
      <View style={styles.caseFooter}>
        <View style={styles.scoreContainer}>
          <Text style={styles.scoreLabel}>LexScore</Text>
          <Text style={styles.scoreValue}>{item.lex_score || 0}</Text>
        </View>
        <View style={styles.statsRow}>
          <Text style={styles.statText}>
            <Icon name="eye-outline" size={14} /> {item.view_count || 0}
          </Text>
          <Text style={styles.statText}>
            <Icon name="star-outline" size={14} /> {item.favorite_count || 0}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View style={styles.logoSection}>
            <Text style={styles.logoIcon}>⚖️</Text>
            <View>
              <Text style={styles.brandName}>LexPrime</Text>
              <Text style={styles.brandSlogan}>智能法律助手</Text>
            </View>
          </View>
          <TouchableOpacity
            style={styles.avatarContainer}
            onPress={() => navigation.navigate('Profile', {screen: 'ProfileMain'})}>
            {isAuthenticated && user?.avatar_url ? (
              <Image source={{uri: user.avatar_url}} style={styles.avatar} />
            ) : (
              <View style={styles.avatarPlaceholder}>
                <Icon name="person-outline" size={24} color={COLORS.light.primary} />
              </View>
            )}
          </TouchableOpacity>
        </View>

        <View style={styles.searchBar}>
          <Icon name="search-outline" size={20} color={COLORS.light.textSecondary} />
          <TextInput
            style={styles.searchInput}
            placeholder="搜索判例、法规、企业..."
            placeholderTextColor={COLORS.light.textLight}
            value={searchKeyword}
            onChangeText={setSearchKeyword}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          <TouchableOpacity style={styles.searchBtn} onPress={handleSearch}>
            <Text style={styles.searchBtnText}>搜索</Text>
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.quickActions}>
          <View style={styles.actionGrid}>
            {quickActions.map(action => (
              <TouchableOpacity
                key={action.id}
                style={styles.actionItem}
                onPress={() => handleQuickAction(action.action)}
                activeOpacity={0.7}>
                <View style={[styles.actionIcon, {backgroundColor: action.color + '20'}]}>
                  <Icon name={action.icon} size={28} color={action.color} />
                </View>
                <Text style={styles.actionText}>{action.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.statsCard}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{stats.totalCases}</Text>
            <Text style={styles.statLabel}>判例总量</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{stats.todaySchedule}</Text>
            <Text style={styles.statLabel}>今日日程</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>{stats.pendingReview}</Text>
            <Text style={styles.statLabel}>待审查</Text>
          </View>
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>🔥 热门判例</Text>
            <TouchableOpacity
              onPress={() => navigation.navigate('Cases', {screen: 'CasesList'})}>
              <Text style={styles.sectionMore}>查看更多 ›</Text>
            </TouchableOpacity>
          </View>

          {loading && hotCases.length === 0 ? (
            <ActivityIndicator style={styles.loading} color={COLORS.light.primary} />
          ) : (
            <FlatList
              data={hotCases}
              renderItem={renderCaseItem}
              keyExtractor={item => item.id?.toString() || item.doc_id}
              scrollEnabled={false}
              ItemSeparatorComponent={() => <View style={{height: 16}} />}
            />
          )}
        </View>

        {isAuthenticated && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>📅 今日日程</Text>
              <TouchableOpacity onPress={() => navigation.navigate('Schedule')}>
                <Text style={styles.sectionMore}>全部 ›</Text>
              </TouchableOpacity>
            </View>

            {todayLoading ? (
              <ActivityIndicator style={styles.loading} color={COLORS.light.primary} />
            ) : todayList.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyIcon}>📭</Text>
                <Text style={styles.emptyText}>今日暂无日程</Text>
              </View>
            ) : (
              todayList.map(item => (
                <View key={item.id} style={styles.scheduleItem}>
                  <View style={styles.scheduleTime}>
                    <Text style={styles.timeText}>{item.time || '全天'}</Text>
                  </View>
                  <View style={styles.scheduleContent}>
                    <Text style={styles.scheduleTitle}>{item.title}</Text>
                    <Text style={styles.scheduleType}>
                      {item.type === 'court'
                        ? '开庭'
                        : item.type === 'meeting'
                        ? '会议'
                        : '其他'}
                    </Text>
                  </View>
                </View>
              ))
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.light.background,
  },
  header: {
    backgroundColor: COLORS.light.primary,
    paddingHorizontal: SIZES.padding,
    paddingTop: 20,
    paddingBottom: 30,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  logoSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  logoIcon: {
    fontSize: 36,
  },
  brandName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
  },
  brandSlogan: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  avatarContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    overflow: 'hidden',
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatar: {
    width: '100%',
    height: '100%',
  },
  avatarPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 4,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 14,
    color: COLORS.light.text,
  },
  searchBtn: {
    backgroundColor: COLORS.light.primary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  searchBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  quickActions: {
    paddingHorizontal: SIZES.padding,
    marginTop: -20,
  },
  actionGrid: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    justifyContent: 'space-around',
    ...SHADOWS.medium,
  },
  actionItem: {
    alignItems: 'center',
    gap: 8,
  },
  actionIcon: {
    width: 52,
    height: 52,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionText: {
    fontSize: 12,
    color: COLORS.light.textSecondary,
  },
  statsCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: SIZES.padding,
    marginTop: 20,
    borderRadius: 16,
    padding: 20,
    ...SHADOWS.small,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.light.primary,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.light.textSecondary,
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    backgroundColor: COLORS.light.borderLight,
  },
  section: {
    paddingHorizontal: SIZES.padding,
    marginTop: 28,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.light.text,
  },
  sectionMore: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
  },
  caseCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    ...SHADOWS.small,
  },
  caseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 10,
  },
  caseName: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.light.text,
    lineHeight: 22,
  },
  causeBadge: {
    backgroundColor: COLORS.light.primary + '15',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  causeText: {
    fontSize: 11,
    color: COLORS.light.primary,
    fontWeight: '500',
  },
  caseInfo: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
  },
  courtText: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
  },
  dateText: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
  },
  caseFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.light.borderLight,
  },
  scoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  scoreLabel: {
    fontSize: 12,
    color: COLORS.light.textLight,
  },
  scoreValue: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.light.warning,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 16,
  },
  statText: {
    fontSize: 12,
    color: COLORS.light.textLight,
  },
  loading: {
    padding: 30,
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#fff',
    borderRadius: 16,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: 14,
    color: COLORS.light.textLight,
  },
  scheduleItem: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 16,
    ...SHADOWS.small,
  },
  scheduleTime: {
    width: 70,
    paddingTop: 2,
  },
  timeText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.light.primary,
  },
  scheduleContent: {
    flex: 1,
  },
  scheduleTitle: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.light.text,
    marginBottom: 4,
  },
  scheduleType: {
    fontSize: 12,
    color: COLORS.light.textLight,
  },
});

export default HomeScreen;
