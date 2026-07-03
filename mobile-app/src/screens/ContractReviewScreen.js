import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
} from 'react-native';
import {useSelector} from 'react-redux';
import {SafeAreaView} from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import {launchImageLibrary, launchCamera} from 'react-native-image-picker';

import {COLORS, SIZES, SHADOWS} from '../theme';
import {contractReviewApi} from '../api';

const contractTypes = [
  '借款合同',
  '买卖合同',
  '租赁合同',
  '劳动合同',
  '服务合同',
  '技术合同',
  '建设工程合同',
  '其他',
];

const stances = ['审查方', '甲方', '乙方'];

const ContractReviewScreen = ({navigation}) => {
  const {isAuthenticated} = useSelector(state => state.auth);

  const [contractType, setContractType] = useState('');
  const [stance, setStance] = useState('审查方');
  const [contractText, setContractText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [reviewResult, setReviewResult] = useState(null);
  const [reviewId, setReviewId] = useState('');
  const [showTypePicker, setShowTypePicker] = useState(false);
  const [showStancePicker, setShowStancePicker] = useState(false);

  const handleImagePick = async source => {
    if (!isAuthenticated) {
      navigation.navigate('Profile', {screen: 'Login'});
      return;
    }

    const options = {
      mediaType: 'photo',
      quality: 0.8,
      maxWidth: 2000,
      maxHeight: 2000,
    };

    try {
      let result;
      if (source === 'camera') {
        result = await launchCamera(options);
      } else {
        result = await launchImageLibrary(options);
      }

      if (result.assets && result.assets.length > 0) {
        const uri = result.assets[0].uri;
        await uploadImage(uri);
      }
    } catch (error) {
      console.error('选择图片失败', error);
    }
  };

  const uploadImage = async uri => {
    try {
      setIsAnalyzing(true);
      const formData = new FormData();
      formData.append('file', {
        uri: uri,
        type: 'image/jpeg',
        name: 'contract.jpg',
      });

      const res = await contractReviewApi.ocrImage(formData);
      if (res.contract_text) {
        setContractText(res.contract_text);
      }
    } catch (error) {
      console.error('OCR 识别失败', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleStartReview = async () => {
    if (!isAuthenticated) {
      navigation.navigate('Profile', {screen: 'Login'});
      return;
    }

    if (!contractText.trim()) {
      return;
    }

    if (!contractType) {
      return;
    }

    setIsAnalyzing(true);
    setReviewResult(null);

    try {
      const res = await contractReviewApi.uploadContract({
        contract_type: contractType,
        contract_text: contractText,
        stance: stance,
      });

      if (res.review_id) {
        setReviewId(res.review_id);
        const result = await contractReviewApi.getResult(res.review_id);
        setReviewResult(result);
      }
    } catch (error) {
      console.error('合同审查失败', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setContractType('');
    setContractText('');
    setReviewResult(null);
    setReviewId('');
  };

  const handleExport = async format => {
    try {
      await contractReviewApi.exportReport(reviewId, format);
    } catch (error) {
      console.error('导出失败', error);
    }
  };

  const getRiskColor = level => {
    switch (level) {
      case 'high':
        return COLORS.light.danger;
      case 'medium':
        return COLORS.light.warning;
      default:
        return COLORS.light.success;
    }
  };

  const getRiskBgColor = level => {
    switch (level) {
      case 'high':
        return COLORS.light.danger + '15';
      case 'medium':
        return COLORS.light.warning + '15';
      default:
        return COLORS.light.success + '15';
    }
  };

  const getRiskLabel = level => {
    switch (level) {
      case 'high':
        return '高风险';
      case 'medium':
        return '中风险';
      default:
        return '低风险';
    }
  };

  if (reviewResult) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>审查结果</Text>
        </View>

        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={styles.resultHeader}>
            <View>
              <Text style={styles.resultTitle}>审查结果</Text>
              <Text style={styles.resultSubtitle}>
                {reviewResult.contract_type || contractType}
              </Text>
            </View>
            <View style={styles.scoreBadge}>
              <Text style={styles.scoreLabel}>风险评分</Text>
              <Text style={[styles.scoreValue, {color: getRiskColor('high')}]}>
                {reviewResult.risk_score || 0}
              </Text>
            </View>
          </View>

          <View style={styles.summaryCard}>
            <Text style={styles.cardTitle}>审查摘要</Text>
            <Text style={styles.summaryText}>
              {reviewResult.summary || '已完成合同审查，发现以下风险点。'}
            </Text>
          </View>

          <View style={styles.risksSection}>
            <View style={styles.sectionHeaderRow}>
              <Text style={styles.cardTitle}>风险点</Text>
              <Text style={styles.riskCount}>
                {reviewResult.risks?.length || 0} 项
              </Text>
            </View>

            {reviewResult.risks?.map((risk, index) => (
              <View key={index} style={styles.riskItem}>
                <View style={styles.riskHeader}>
                  <View
                    style={[
                      styles.riskLevelBadge,
                      {backgroundColor: getRiskBgColor(risk.level)},
                    ]}>
                    <Text
                      style={[
                        styles.riskLevelText,
                        {color: getRiskColor(risk.level)},
                      ]}>
                      {getRiskLabel(risk.level)}
                    </Text>
                  </View>
                  <Text style={styles.riskTitle} numberOfLines={1}>
                    {risk.title || risk.clause || `风险点 ${index + 1}`}
                  </Text>
                </View>
                <Text style={styles.riskDesc} numberOfLines={2}>
                  {risk.description || risk.detail}
                </Text>
              </View>
            ))}
          </View>

          <View style={styles.actionButtons}>
            <TouchableOpacity style={styles.outlineBtn} onPress={handleReset}>
              <Text style={styles.outlineBtnText}>重新审查</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.primaryBtn}
              onPress={() => handleExport('pdf')}>
              <Text style={styles.primaryBtnText}>导出报告</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>合同审查</Text>
      </View>

      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.inputSection}>
          <Text style={styles.sectionTitle}>合同信息</Text>

          <TouchableOpacity
            style={styles.pickerField}
            onPress={() => setShowTypePicker(!showTypePicker)}>
            <Text style={styles.pickerLabel}>合同类型</Text>
            <View style={styles.pickerValueRow}>
              <Text
                style={[
                  styles.pickerValue,
                  !contractType && styles.pickerPlaceholder,
                ]}>
                {contractType || '请选择合同类型'}
              </Text>
              <Icon
                name={showTypePicker ? 'chevron-up' : 'chevron-down'}
                size={18}
                color={COLORS.light.textSecondary}
              />
            </View>
          </TouchableOpacity>

          {showTypePicker && (
            <View style={styles.pickerOptions}>
              {contractTypes.map(type => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.pickerOption,
                    contractType === type && styles.pickerOptionActive,
                  ]}
                  onPress={() => {
                    setContractType(type);
                    setShowTypePicker(false);
                  }}>
                  <Text
                    style={[
                      styles.pickerOptionText,
                      contractType === type && styles.pickerOptionTextActive,
                    ]}>
                    {type}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          <TouchableOpacity
            style={styles.pickerField}
            onPress={() => setShowStancePicker(!showStancePicker)}>
            <Text style={styles.pickerLabel}>审查立场</Text>
            <View style={styles.pickerValueRow}>
              <Text style={styles.pickerValue}>{stance}</Text>
              <Icon
                name={showStancePicker ? 'chevron-up' : 'chevron-down'}
                size={18}
                color={COLORS.light.textSecondary}
              />
            </View>
          </TouchableOpacity>

          {showStancePicker && (
            <View style={styles.pickerOptions}>
              {stances.map(s => (
                <TouchableOpacity
                  key={s}
                  style={[
                    styles.pickerOption,
                    stance === s && styles.pickerOptionActive,
                  ]}
                  onPress={() => {
                    setStance(s);
                    setShowStancePicker(false);
                  }}>
                  <Text
                    style={[
                      styles.pickerOptionText,
                      stance === s && styles.pickerOptionTextActive,
                    ]}>
                    {s}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          <Text style={styles.pickerLabel}>合同内容</Text>
          <TextInput
            style={styles.textArea}
            placeholder="请粘贴合同文本，或点击下方按钮上传图片/文件"
            placeholderTextColor={COLORS.light.textLight}
            value={contractText}
            onChangeText={setContractText}
            multiline
            textAlignVertical="top"
            maxLength={50000}
          />

          <View style={styles.uploadButtons}>
            <TouchableOpacity
              style={styles.uploadBtn}
              onPress={() => handleImagePick('camera')}>
              <Icon name="camera-outline" size={28} color={COLORS.light.primary} />
              <Text style={styles.uploadText}>拍照</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.uploadBtn}
              onPress={() => handleImagePick('library')}>
              <Icon name="image-outline" size={28} color={COLORS.light.primary} />
              <Text style={styles.uploadText}>图片</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.uploadBtn}>
              <Icon name="document-outline" size={28} color={COLORS.light.primary} />
              <Text style={styles.uploadText}>文件</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.submitBtn, isAnalyzing && styles.submitBtnDisabled]}
            onPress={handleStartReview}
            disabled={isAnalyzing}>
            {isAnalyzing ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color="#fff" size="small" />
                <Text style={styles.submitBtnText}>审查中...</Text>
              </View>
            ) : (
              <Text style={styles.submitBtnText}>开始审查</Text>
            )}
          </TouchableOpacity>
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
  inputSection: {
    padding: SIZES.padding,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.light.text,
    marginBottom: 20,
  },
  pickerField: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.light.border,
  },
  pickerLabel: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
    marginBottom: 8,
  },
  pickerValueRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pickerValue: {
    fontSize: 16,
    color: COLORS.light.text,
  },
  pickerPlaceholder: {
    color: COLORS.light.textLight,
  },
  pickerOptions: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.light.border,
    overflow: 'hidden',
  },
  pickerOption: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.light.borderLight,
  },
  pickerOptionActive: {
    backgroundColor: COLORS.light.primary + '10',
  },
  pickerOption:last-child: {
    borderBottomWidth: 0,
  },
  pickerOptionText: {
    fontSize: 15,
    color: COLORS.light.text,
  },
  pickerOptionTextActive: {
    color: COLORS.light.primary,
    fontWeight: '500',
  },
  textArea: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    minHeight: 150,
    fontSize: 14,
    color: COLORS.light.text,
    borderWidth: 1,
    borderColor: COLORS.light.border,
    marginBottom: 16,
  },
  uploadButtons: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 24,
  },
  uploadBtn: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingVertical: 20,
    alignItems: 'center',
    gap: 8,
    borderWidth: 2,
    borderColor: COLORS.light.border,
    borderStyle: 'dashed',
  },
  uploadText: {
    fontSize: 12,
    color: COLORS.light.textSecondary,
  },
  submitBtn: {
    backgroundColor: COLORS.light.primary,
    borderRadius: 12,
    paddingVertical: 18,
    alignItems: 'center',
  },
  submitBtnDisabled: {
    opacity: 0.6,
  },
  submitBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  resultHeader: {
    backgroundColor: '#fff',
    margin: SIZES.padding,
    marginBottom: 0,
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...SHADOWS.small,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.light.text,
    marginBottom: 4,
  },
  resultSubtitle: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
  },
  scoreBadge: {
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 12,
    color: COLORS.light.textLight,
    marginBottom: 4,
  },
  scoreValue: {
    fontSize: 28,
    fontWeight: '700',
  },
  summaryCard: {
    backgroundColor: '#fff',
    marginHorizontal: SIZES.padding,
    marginTop: 16,
    borderRadius: 16,
    padding: 20,
    ...SHADOWS.small,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.light.text,
    marginBottom: 12,
  },
  summaryText: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
    lineHeight: 22,
  },
  risksSection: {
    paddingHorizontal: SIZES.padding,
    marginTop: 20,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  riskCount: {
    fontSize: 14,
    color: COLORS.light.textSecondary,
  },
  riskItem: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    ...SHADOWS.small,
  },
  riskHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  riskLevelBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskLevelText: {
    fontSize: 11,
    fontWeight: '600',
  },
  riskTitle: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.light.text,
  },
  riskDesc: {
    fontSize: 13,
    color: COLORS.light.textSecondary,
    lineHeight: 20,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 16,
    padding: SIZES.padding,
  },
  outlineBtn: {
    flex: 1,
    borderWidth: 2,
    borderColor: COLORS.light.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  outlineBtnText: {
    color: COLORS.light.primary,
    fontSize: 15,
    fontWeight: '600',
  },
  primaryBtn: {
    flex: 1,
    backgroundColor: COLORS.light.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
});

export default ContractReviewScreen;
