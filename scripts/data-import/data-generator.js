'use strict';

var DataGenerator = (function () {
    var caseNames = [
        '借款合同纠纷案', '买卖合同纠纷案', '租赁合同纠纷案', '承揽合同纠纷案',
        '建设工程施工合同纠纷案', '物业服务合同纠纷案', '股权转让纠纷案',
        '劳动合同纠纷案', '交通事故责任纠纷案', '医疗损害责任纠纷案',
        '知识产权侵权纠纷案', '不正当竞争纠纷案', '公司决议效力确认纠纷案',
        '股东知情权纠纷案', '合伙协议纠纷案', '保险合同纠纷案',
        '担保合同纠纷案', '委托合同纠纷案', '居间合同纠纷案', '行纪合同纠纷案'
    ];

    var courts = [
        '北京市第一中级人民法院', '北京市第二中级人民法院', '上海市第一中级人民法院',
        '上海市第二中级人民法院', '广州市中级人民法院', '深圳市中级人民法院',
        '杭州市中级人民法院', '南京市中级人民法院', '成都市中级人民法院',
        '武汉市中级人民法院', '北京市朝阳区人民法院', '上海市浦东新区人民法院',
        '广州市天河区人民法院', '深圳市南山区人民法院', '杭州市西湖区人民法院'
    ];

    var causes = [
        { name: '借款合同纠纷', category: '合同纠纷', color: '#ef4444' },
        { name: '买卖合同纠纷', category: '合同纠纷', color: '#f97316' },
        { name: '租赁合同纠纷', category: '合同纠纷', color: '#eab308' },
        { name: '承揽合同纠纷', category: '合同纠纷', color: '#22c55e' },
        { name: '建设工程施工合同纠纷', category: '合同纠纷', color: '#14b8a6' },
        { name: '物业服务合同纠纷', category: '合同纠纷', color: '#3b82f6' },
        { name: '股权转让纠纷', category: '与公司有关的纠纷', color: '#8b5cf6' },
        { name: '劳动合同纠纷', category: '劳动争议', color: '#ec4899' },
        { name: '交通事故责任纠纷', category: '侵权责任纠纷', color: '#f43f5e' },
        { name: '医疗损害责任纠纷', category: '侵权责任纠纷', color: '#6366f1' }
    ];

    var lawTitles = [
        { title: '中华人民共和国民法典', type: '法律', level: 1 },
        { title: '中华人民共和国刑法', type: '法律', level: 1 },
        { title: '中华人民共和国民事诉讼法', type: '法律', level: 1 },
        { title: '中华人民共和国刑事诉讼法', type: '法律', level: 1 },
        { title: '中华人民共和国行政诉讼法', type: '法律', level: 1 },
        { title: '中华人民共和国公司法', type: '法律', level: 1 },
        { title: '中华人民共和国合同法', type: '法律', level: 1 },
        { title: '中华人民共和国物权法', type: '法律', level: 1 },
        { title: '中华人民共和国劳动合同法', type: '法律', level: 1 },
        { title: '中华人民共和国社会保险法', type: '法律', level: 1 },
        { title: '中华人民共和国道路交通安全法', type: '法律', level: 1 },
        { title: '中华人民共和国保险法', type: '法律', level: 1 },
        { title: '中华人民共和国专利法', type: '法律', level: 1 },
        { title: '中华人民共和国商标法', type: '法律', level: 1 },
        { title: '中华人民共和国著作权法', type: '法律', level: 1 },
        { title: '中华人民共和国反不正当竞争法', type: '法律', level: 1 },
        { title: '中华人民共和国消费者权益保护法', type: '法律', level: 1 },
        { title: '中华人民共和国产品质量法', type: '法律', level: 1 },
        { title: '中华人民共和国食品安全法', type: '法律', level: 1 },
        { title: '中华人民共和国环境保护法', type: '法律', level: 1 }
    ];

    var companyNames = [
        '北京科技有限公司', '上海信息技术有限公司', '广州电子科技有限公司',
        '深圳软件开发有限公司', '杭州网络科技有限公司', '南京智能科技有限公司',
        '成都数据科技有限公司', '武汉云计算有限公司', '西安人工智能有限公司',
        '重庆区块链技术有限公司', '天津生物科技有限公司', '苏州新材料有限公司',
        '宁波国际贸易有限公司', '青岛海洋科技有限公司', '大连装备制造有限公司',
        '厦门新能源有限公司', '福州医药科技有限公司', '济南环保科技有限公司',
        '郑州农业科技有限公司', '长沙文化传媒有限公司'
    ];

    var industries = [
        '软件和信息技术服务业', '互联网和相关服务', '计算机、通信和其他电子设备制造业',
        '医药制造业', '专业技术服务业', '商务服务业', '金融业', '房地产业',
        '建筑业', '批发和零售业', '交通运输、仓储和邮政业', '住宿和餐饮业',
        '租赁和商务服务业', '科学研究和技术服务业', '水利、环境和公共设施管理业'
    ];

    var regions = [
        '北京市', '上海市', '广东省', '江苏省', '浙江省', '四川省', '湖北省',
        '山东省', '河南省', '福建省', '陕西省', '重庆市', '天津市', '辽宁省',
        '湖南省', '安徽省', '江西省', '河北省', '山西省', '黑龙江省'
    ];

    var lawyerNames = [
        '张明', '李华', '王芳', '刘强', '陈静', '杨帆', '赵磊', '黄敏',
        '周涛', '吴婷', '徐鹏', '孙丽', '马超', '朱琳', '胡军', '郭燕',
        '林峰', '何雪', '高翔', '罗梅'
    ];

    var specialties = [
        '民商事诉讼', '刑事辩护', '公司法律事务', '知识产权', '劳动法',
        '房地产与建筑工程', '金融与银行', '婚姻家庭', '交通事故', '医疗纠纷',
        '合同纠纷', '企业合规', '并购重组', '破产清算', '海商海事'
    ];

    function randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function randomPick(arr) {
        return arr[Math.floor(Math.random() * arr.length)];
    }

    function randomDate(startYear, endYear) {
        var year = randomInt(startYear, endYear);
        var month = randomInt(1, 12);
        var day = randomInt(1, 28);
        return year + '-' + String(month).padStart(2, '0') + '-' + String(day).padStart(2, '0');
    }

    function generateCase(index) {
        var cause = randomPick(causes);
        var caseName = randomPick(caseNames);
        var year = randomInt(2018, 2025);
        var court = randomPick(courts);
        var caseNumber = '(' + year + ')京' + randomInt(1, 5) + '民初' + (1000 + index) + '号';

        return {
            doc_id: 'case-gen-' + (Date.now() + index),
            case_id: caseNumber,
            case_name: '张三诉李四' + caseName,
            court: court,
            cause: cause.name,
            cause_category: cause.category,
            cause_color: cause.color,
            judgment_date: randomDate(2018, 2025),
            year: year,
            lex_score: randomInt(60, 95),
            view_count: randomInt(10, 500),
            favorite_count: randomInt(1, 50),
            parties: '原告：张三；被告：李四',
            legal_basis: '《民法典》第五百七十七条',
            full_text: '原告张三与被告李四于' + randomDate(2020, 2023) + '签订合同...',
            source: '模拟数据',
            source_url: '',
            keywords: [cause.name.split('纠纷')[0], '合同', '违约']
        };
    }

    function generateCases(count) {
        var cases = [];
        for (var i = 0; i < count; i++) {
            cases.push(generateCase(i));
        }
        return cases;
    }

    function generateLaw(index) {
        var law = randomPick(lawTitles);
        return {
            law_id: 'law-gen-' + (Date.now() + index),
            title: law.title,
            law_type: law.type,
            status: '现行有效',
            issue_date: randomDate(1990, 2020),
            effective_date: randomDate(1991, 2021),
            level: law.level,
            source: '模拟数据',
            source_url: '',
            summary: law.title + '的简要说明...',
            full_text: '第一章 总则\n\n第一条 为了...'
        };
    }

    function generateLaws(count) {
        var laws = [];
        for (var i = 0; i < count; i++) {
            laws.push(generateLaw(i));
        }
        return laws;
    }

    function generateCompany(index) {
        var baseName = randomPick(companyNames);
        var fullName = baseName.replace('有限公司', randomPick(['股份有限公司', '有限责任公司', '集团有限公司']));
        return {
            unified_id: '91' + randomInt(100000, 999999) + 'MA01ABC' + String(index).padStart(3, '0'),
            company_name: fullName,
            company_type: randomPick(['有限责任公司', '股份有限公司', '合伙企业', '个人独资企业']),
            legal_rep: randomPick(lawyerNames),
            registered_capital: randomInt(100, 10000) + '万元',
            paid_capital: randomInt(50, 8000) + '万元',
            establish_date: randomDate(2000, 2023),
            business_status: randomPick(['存续', '在业', '注销', '吊销']),
            registered_address: randomPick(regions) + randomPick(['朝阳区', '海淀区', '浦东新区', '天河区', '南山区', '西湖区']) + randomInt(1, 999) + '号',
            business_scope: '技术开发、技术咨询、技术服务、技术转让；软件开发；数据处理；企业管理咨询；',
            industry: randomPick(industries),
            region: randomPick(regions),
            is_zxgk: Math.random() < 0.1,
            is_dishonest: Math.random() < 0.05,
            source: '模拟数据',
            source_url: '',
            view_count: randomInt(5, 200)
        };
    }

    function generateCompanies(count) {
        var companies = [];
        for (var i = 0; i < count; i++) {
            companies.push(generateCompany(i));
        }
        return companies;
    }

    function generateLawyer(index) {
        var name = randomPick(lawyerNames);
        var specCount = randomInt(1, 3);
        var lawyerSpecialties = [];
        for (var i = 0; i < specCount; i++) {
            var spec = randomPick(specialties);
            if (lawyerSpecialties.indexOf(spec) === -1) {
                lawyerSpecialties.push(spec);
            }
        }
        return {
            id: 'lawyer-gen-' + (Date.now() + index),
            name: name,
            email: 'lawyer' + index + '@example.com',
            phone: '138' + String(randomInt(10000000, 99999999)),
            role: randomPick(['合伙人', '资深律师', '律师', '实习律师']),
            specialties: lawyerSpecialties,
            firm_id: 'firm-gen-001',
            firm_name: '精诚律师事务所',
            avatar_url: '',
            license_number: '11010' + String(randomInt(10000, 99999)),
            practice_years: randomInt(1, 25),
            education: randomPick(['法学学士', '法学硕士', '法学博士']),
            bio: name + '律师，执业' + randomInt(1, 25) + '年，擅长' + lawyerSpecialties.join('、') + '。',
            rating: randomInt(30, 50) / 10,
            case_count: randomInt(50, 500),
            win_rate: randomInt(50, 95),
            is_active: true,
            region: randomPick(regions),
            hourly_rate: randomInt(500, 3000)
        };
    }

    function generateLawyers(count) {
        var lawyers = [];
        for (var i = 0; i < count; i++) {
            lawyers.push(generateLawyer(i));
        }
        return lawyers;
    }

    return {
        generateCases: generateCases,
        generateLaws: generateLaws,
        generateCompanies: generateCompanies,
        generateLawyers: generateLawyers,
        randomInt: randomInt,
        randomPick: randomPick,
        randomDate: randomDate
    };
})();

if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataGenerator;
}
