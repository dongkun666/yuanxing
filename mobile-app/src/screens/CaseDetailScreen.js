import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Share,
} from 'react-native';
import {useSelector, useDispatch} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';

import {COLORS, SIZES, SHADOWS} from '../theme';
import {fetchCaseDetail, resetDetail} from '../store/slices/casesSlice';
import {casesApi} from '../api';

const CaseDetailScreen = ({route, navigation}) => {
  const {docId} = route.params;
  const dispatch = useDispatch();
  const {detail, detailLoading} = useSelector(state => state.cases);
  const {isAuthenticated} = useSelector(state => state.auth);

  const [showFullText, setShowFullText] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);

  useEffect(() => {
    dispatch(fetchCaseDetail(docId));
    return () => {
      dispatch(resetDetail());
    };
  }, [docId]);

  const toggleFavorite = async () => {
    if (!isAuthenticated) {
      navigation.navigate('Profile', {screen: 'Login'});
      return;
    }
    try {
      if (isFavorite) {
        await casesApi.removeFavorite(docId);
      } else {
        await casesApi.toggleFavorite(docId);
      }
      setIsFavorite(!isFavorite);
    } catch (error) {
      console.error('收藏操作失败', error);
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        title: detail?.case_name || 'LexPrime 判例详情',
        message: `【${detail?.case_name}】\n${detail?.court}\n${detail?.judgment_date}\n\n查看详情: https://lexprime.com/cases/${docId}`,
      });
    } catch (error) {
      console.error('分享失败', error);
    }
  };

  const handleExport = format => {
    console.log('导出格式:', format);
  };

  const showExportOptions = () => {
    // 可以用 ActionSheet 实现
    handleExport('pdf');
  };

  if (detailLoading) {
    return (
      <View style={[styles.container, styles.loadingContainer]}>
        <ActivityIndicator size="large" color={COLORS.light.primary} />
      </View>
    );
  }

  if (!detail) {
    return (
      <View style={[styles.container, styles.loadingContainer]}>
        <Text style={styles.emptyText}>案件不存在</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color={COLORS.light.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>案件详情</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerBtn} onPress={toggleFavorite}>
            <Icon
              name={isFavorite ? 'heart' : 'heart-outline'}
              size={22}
              color={isFavorite ? COLORS.light.danger : COLORS.light.textSecondary}
            />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerBtn} onPress={handleShare}>
            <Icon name="share-outline" size={22} color={COLORS.light.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerBtn} onPress={showExportOptions}>
            <Icon name="download-outline" size={22} color={COLORS.light.textSecondary} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.caseHeader}>
          <Text style={styles.caseTitle}>{detail.case_name}</Text>
          
          <View style={styles.metaGrid}>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>案号</Text>
              <Text style={styles.metaValue}>{detail.case_id}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>法院</Text>
              <Text style={styles.metaValue}>{detail.court}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>判决日期</Text>
              <Text style={styles.metaValue}>{detail.judgment_date}</Text>
            </View>
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>案由</Text>
              <View style={styles.causeBadge}>
                <Text style={styles.causeText}>{detail.cause}</Text>
              </View>
            </View>
          </View>

          <View style={styles.scoreRow}>
            <View style={styles.scoreBox}>
              <Text style={styles.scoreLabel}>LexScore</Text>
              <Text style={styles.scoreValue}>{detail.lex_score || 0}</Text>
            </View>
            <View style={styles.statsRow}>
              <Text style={styles.statItem}>
                <Icon name="eye-outline" size={14} /> {detail.view_count || 0} 浏览
              </Text>
              <Text style={styles.statItem}>
                <Icon name="star-outline" size={14} /> {detail.favorite_count || 0} 收藏
              </Text>
            </View>
          </View>
        </View>

        {detail.parties && (
          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>当事人</Text>
            <Text style={styles.sectionContent}>{detail.parties}</Text>
          </View>
        )}

        {detail.legal_basis && (
          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>法律依据</Text>
            <Text style={styles.sectionContent}>{detail.legal_basis}</Text>
          </View>
        )}

        {detail.keywords && detail.keywords.length > 0 && (
          <View style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>关键词</Text>
            <View style={styles.keywordsContainer}>
              {detail.keywords.map((keyword, index) => (
                <View key={index} style={styles.keywordTag}>
                  <Text style={styles.keywordText}>{keyword}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        <View style={styles.sectionCard}>
          <TouchableOpacity
            style={styles.sectionHeader}
            onPress={() => setShowFullText(!showFullText)}>
            <Text style={styles.sectionTitle}>判决书全文</Text>
            <View style={styles.toggleBtn}>
              <Text style={styles.toggleText}>
                {showFullText ? '收起' : '展开'}
              </Text>
              <Icon
                name={showFullText ? 'chevron-up' : 'chevron-down'}
                size={16}
                color={COLORS.light.primary}
              />
            </View>
          </TouchableOpacity>
          <Text
            style={[
              styles.fullText,
              !showFullText && styles.fullTextCollapsed,
            ]}
            numberOfLines={showFullText ? undefined : 5}>
            {detail.full_text}
          </Text>
        </View>

        <View style={{height: 40}} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.light.background,
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 8,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.light.borderLight,
  },
  backBtn: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.light.text,
    textAlign: 'center',
  },
  headerActions: {
    flexDirection: 'row',
    paddingRight: 8,
  },
  headerBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  caseHeader: {
    backgroundColor: '#fff',
    margin: SIZES.padding,
    marginBottom: 0,
    borderRadius: 16,
    padding: 20,
    ...SHADOWS.small,
  },
  caseTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.light.text,
    lineHeight: 28,
    marginBottom: 20,
  },
  metaGrid: {
    gap: 12,
    marginBottom: 20,
    padding: 16,
    backgroundColor: COLORS.light.background,
    borderRadius: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metaLabel: {
    width: 70,
    fontSize: 13,
    color: COLORS.light.textSecondary,
  },
  metaValue: {
    flex: 1,
    fontSize: 13,
    color: COLORS.light.text,
  },
  causeBadge: {
    backgroundColor: COLORS.light.primary + '15',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  causeText: {
    fontSize: 12,
    color: COLORS.light.primary,
    fontWeight: '500',
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.light.borderLight,
  },
  scoreBox: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 6,
  },
  scoreLabel: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
  },
  scoreValue: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.light.warning,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 20,
  },
  statItem: {
    fontSize: 12,
    color: COLORS.light.textLight,
  },
  sectionCard: {
    backgroundColor: '#fff',
    marginHorizontal: SIZES.padding,
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    ...SHADOWS.small,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.light.text,
    marginBottom: 12,
  },
  sectionHeader .sectionTitle: {
    marginBottom: 0,
  },
  sectionContent: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
    lineHeight: 22,
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  keywordTag: {
    backgroundColor: COLORS.light.primary + '15',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  keywordText: {
    fontSize: 12,
    color: COLORS.light.primary,
  },
  toggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  toggleText: {
    fontSize: 13,
    color: COLORS.light.primary,
  },
  fullText: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
    lineHeight: 24,
  },
  fullTextCollapsed: {
    overflow: 'hidden',
  },
  emptyText: {
    fontSize: 14,
    color: COLORS.light.textLight,
  },
});

export default CaseDetailScreen;
