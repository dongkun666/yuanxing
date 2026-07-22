import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import {useSelector, useDispatch} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';

import {COLORS, SIZES, SHADOWS} from '../theme';
import {fetchCases, resetCases} from '../store/slices/casesSlice';

const categories = [
  {label: '全部', value: ''},
  {label: '合同纠纷', value: '合同纠纷'},
  {label: '侵权纠纷', value: '侵权纠纷'},
  {label: '婚姻家庭', value: '婚姻家庭'},
  {label: '劳动争议', value: '劳动争议'},
  {label: '知识产权', value: '知识产权'},
  {label: '刑事', value: '刑事'},
  {label: '行政', value: '行政'},
];

const CasesScreen = ({route, navigation}) => {
  const dispatch = useDispatch();
  const {list, loading, hasMore, page} = useSelector(state => state.cases);

  const [searchKeyword, setSearchKeyword] = useState(route.params?.keyword || '');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    loadCases();
  }, [selectedCategory]);

  const loadCases = () => {
    dispatch(
      fetchCases({
        cause: searchKeyword || undefined,
        cause_category: selectedCategory || undefined,
        limit: 20,
        offset: (page - 1) * 20,
      }),
    );
  };

  const handleSearch = () => {
    dispatch(resetCases());
    loadCases();
  };

  const handleRefresh = () => {
    dispatch(resetCases());
    loadCases();
  };

  const handleLoadMore = () => {
    if (hasMore && !loading) {
      dispatch(fetchCases({
        cause: searchKeyword || undefined,
        cause_category: selectedCategory || undefined,
        limit: 20,
        offset: page * 20,
      }));
    }
  };

  const handleCategorySelect = value => {
    setSelectedCategory(value);
    dispatch(resetCases());
  };

  const handleCasePress = docId => {
    navigation.navigate('CaseDetail', {docId});
  };

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

  const renderFooter = () => {
    if (!loading) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator color={COLORS.light.primary} />
      </View>
    );
  };

  const renderEmpty = () => {
    if (loading) return null;
    return (
      <View style={styles.emptyState}>
        <Text style={styles.emptyIcon}>📚</Text>
        <Text style={styles.emptyText}>暂无判例数据</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>判例检索</Text>
      </View>

      <View style={styles.searchSection}>
        <View style={styles.searchBox}>
          <Icon name="search-outline" size={20} color={COLORS.light.textSecondary} />
          <TextInput
            style={styles.searchInput}
            placeholder="搜索判例关键词..."
            placeholderTextColor={COLORS.light.textLight}
            value={searchKeyword}
            onChangeText={setSearchKeyword}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
        </View>
      </View>

      <View style={styles.categorySection}>
        <FlatList
          data={categories}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={item => item.value}
          renderItem={({item}) => (
            <TouchableOpacity
              style={[
                styles.categoryItem,
                selectedCategory === item.value && styles.categoryActive,
              ]}
              onPress={() => handleCategorySelect(item.value)}>
              <Text
                style={[
                  styles.categoryText,
                  selectedCategory === item.value && styles.categoryTextActive,
                ]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
          contentContainerStyle={styles.categoryList}
        />
      </View>

      <FlatList
        data={list}
        renderItem={renderCaseItem}
        keyExtractor={item => item.id?.toString() || item.doc_id}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={{height: 16}} />}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        ListFooterComponent={renderFooter}
        ListEmptyComponent={renderEmpty}
        refreshControl={
          <RefreshControl
            refreshing={loading && page === 1}
            onRefresh={handleRefresh}
            tintColor={COLORS.light.primary}
          />
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.light.background,
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: SIZES.padding,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.light.borderLight,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.light.text,
  },
  searchSection: {
    paddingHorizontal: SIZES.padding,
    paddingVertical: 12,
    backgroundColor: '#fff',
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.light.background,
    borderRadius: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 14,
    color: COLORS.light.text,
  },
  categorySection: {
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: COLORS.light.borderLight,
  },
  categoryList: {
    paddingHorizontal: SIZES.padding,
    paddingVertical: 12,
    gap: 10,
  },
  categoryItem: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.light.background,
  },
  categoryActive: {
    backgroundColor: COLORS.light.primary,
  },
  categoryText: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
  },
  categoryTextActive: {
    color: '#fff',
    fontWeight: '500',
  },
  listContent: {
    padding: SIZES.padding,
    flexGrow: 1,
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
  footerLoader: {
    padding: 20,
    alignItems: 'center',
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
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
});

export default CasesScreen;
