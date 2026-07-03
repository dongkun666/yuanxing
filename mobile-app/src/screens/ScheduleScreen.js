import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import {useSelector, useDispatch} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';

import {COLORS, SIZES, SHADOWS} from '../theme';
import {fetchSchedule} from '../store/slices/scheduleSlice';

const ScheduleScreen = ({navigation}) => {
  const dispatch = useDispatch();
  const {list, loading} = useSelector(state => state.schedule);

  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    dispatch(fetchSchedule());
  }, []);

  const formatDate = date => {
    return date.toISOString().split('T')[0];
  };

  const getTypeColor = type => {
    switch (type) {
      case 'court':
        return COLORS.light.danger;
      case 'meeting':
        return COLORS.light.primary;
      default:
        return COLORS.light.success;
    }
  };

  const getTypeBgColor = type => {
    switch (type) {
      case 'court':
        return COLORS.light.danger + '15';
      case 'meeting':
        return COLORS.light.primary + '15';
      default:
        return COLORS.light.success + '15';
    }
  };

  const getTypeLabel = type => {
    switch (type) {
      case 'court':
        return '开庭';
      case 'meeting':
        return '会议';
      default:
        return '其他';
    }
  };

  const renderScheduleItem = ({item}) => (
    <TouchableOpacity style={styles.scheduleItem} activeOpacity={0.7}>
      <View style={[styles.typeBadge, {backgroundColor: getTypeBgColor(item.type)}]}>
        <Text style={[styles.typeText, {color: getTypeColor(item.type)}]}>
          {getTypeLabel(item.type)}
        </Text>
      </View>
      <View style={styles.scheduleContent}>
        <Text style={styles.scheduleTitle}>{item.title}</Text>
        <Text style={styles.scheduleTime}>
          {item.date} {item.time || '全天'}
        </Text>
        {item.location && (
          <Text style={styles.scheduleLocation}>
            <Icon name="location-outline" size={12} /> {item.location}
          </Text>
        )}
      </View>
      <Icon name="chevron-forward" size={18} color={COLORS.light.textLight} />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color={COLORS.light.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>日程管理</Text>
        <TouchableOpacity style={styles.addBtn}>
          <Icon name="add" size={24} color={COLORS.light.primary} />
        </TouchableOpacity>
      </View>

      <View style={styles.dateSelector}>
        <TouchableOpacity style={styles.dateNavBtn}>
          <Icon name="chevron-back" size={20} color={COLORS.light.textSecondary} />
        </TouchableOpacity>
        <Text style={styles.currentDate}>{formatDate(selectedDate)}</Text>
        <TouchableOpacity style={styles.dateNavBtn}>
          <Icon name="chevron-forward" size={20} color={COLORS.light.textSecondary} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={list}
        renderItem={renderScheduleItem}
        keyExtractor={item => item.id?.toString()}
        contentContainerStyle={styles.listContent}
        ItemSeparatorComponent={() => <View style={{height: 12}} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📅</Text>
            <Text style={styles.emptyText}>暂无日程</Text>
          </View>
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
  addBtn: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    paddingVertical: 16,
    gap: 24,
  },
  dateNavBtn: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 18,
    backgroundColor: COLORS.light.background,
  },
  currentDate: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.light.text,
  },
  listContent: {
    padding: SIZES.padding,
    flexGrow: 1,
  },
  scheduleItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    gap: 14,
    ...SHADOWS.small,
  },
  typeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  typeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  scheduleContent: {
    flex: 1,
  },
  scheduleTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.light.text,
    marginBottom: 4,
  },
  scheduleTime: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
    marginBottom: 4,
  },
  scheduleLocation: {
    fontSize: 12,
    color: COLORS.light.textLight,
  },
  emptyState: {
    alignItems: 'center',
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

export default ScheduleScreen;
