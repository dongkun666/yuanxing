/**
 * 客户管理模块
 * 包含: 客户分类切换 + 详情页 + 新建/冲突检查
 * 加载: 在 script.js 之前同步加载
 */


function switchClientTab(el, tab) {
    document.querySelectorAll('#view-client .bg-white.rounded-xl.border.border-\\[\\#E5E6EB\\] .flex.items-center.gap-1 button').forEach(function(btn) {
        if (btn.closest('.flex.items-center.gap-1')) {
            btn.classList.remove('bg-[#165DFF]', 'text-white');
            btn.classList.add('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        }
    });
    el.classList.remove('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
    el.classList.add('bg-[#165DFF]', 'text-white');
    // 显示对应客户（实际项目中筛选数据）
}

function openClientDetail(index) {
    var clients = [
        { name: '李明', avatar: '李', grade: 'A 级', gradeClass: '#FFF1F0 text-[#F53F3F]', status: '活跃', phone: '138****1234', cases: '3' },
        { name: '王华', avatar: '王', grade: 'B 级', gradeClass: '#FFF7E6 text-[#FAAD14]', status: '活跃', phone: '139****5678', cases: '2' },
        { name: '某科技有限公司', avatar: '某', grade: 'A 级', gradeClass: '#FFF1F0 text-[#F53F3F]', status: '活跃', phone: '010-8888****', cases: '5' },
        { name: '赵六', avatar: '赵', grade: 'C 级', gradeClass: '#F7F8FA text-[#86909C]', status: '待回访', phone: '136****9012', cases: '1' },
        { name: '张三', avatar: '张', grade: 'C 级', gradeClass: '#F7F8FA text-[#86909C]', status: '静默', phone: '137****3456', cases: '1' }
    ];

    var c = clients[index] || clients[0];

    document.querySelectorAll('.view-content').forEach(function(v) {
        v.classList.add('hidden');
    });

    document.getElementById('view-client-detail').classList.remove('hidden');

    // 填充数据
    document.getElementById('client-detail-name').textContent = c.name;
    document.getElementById('client-detail-name-text').textContent = c.name;
    document.getElementById('client-detail-avatar').textContent = c.avatar;
    document.getElementById('client-detail-grade').textContent = c.grade;
    document.getElementById('client-detail-grade').className = 'text-[10px] font-medium px-2 py-0.5 rounded';
    var gradeParts = c.gradeClass.split(' ');
    gradeParts.forEach(function(cls) { if (cls) document.getElementById('client-detail-grade').classList.add(cls); });
    document.getElementById('client-detail-status').textContent = c.status;
    document.getElementById('client-detail-phone').textContent = c.phone;
    document.getElementById('client-detail-cases').textContent = c.cases;
}

function backToClientList() {
    document.querySelectorAll('.view-content').forEach(function(v) {
        v.classList.add('hidden');
    });
    document.getElementById('view-client').classList.remove('hidden');
}

var _closeNewClientModal = null;

function showNewClientModal() {
    var content = '<div class="space-y-4">' +
        '<div class="grid grid-cols-2 gap-4">' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">客户姓名 <span class="text-red-400">*</span></label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入客户姓名" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">证件类型</label>' +
        '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand appearance-none bg-white transition-colors">' +
        '<option>身份证</option>' +
        '<option>护照</option>' +
        '<option>统一社会信用代码</option>' +
        '</select>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">证件号码 <span class="text-red-400">*</span></label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入证件号码" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">手机号 <span class="text-red-400">*</span></label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入手机号" type="text"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">邮箱</label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入邮箱地址" type="email"/>' +
        '</div>' +
        '<div>' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">客户类型</label>' +
        '<select class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand appearance-none bg-white transition-colors">' +
        '<option>个人客户</option>' +
        '<option>企业客户</option>' +
        '</select>' +
        '</div>' +
        '<div class="col-span-2">' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">地址</label>' +
        '<input class="w-full border border-bg-border rounded-lg px-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand transition-colors" placeholder="请输入地址" type="text"/>' +
        '</div>' +
        '</div>' +
        '<div class="pt-3 border-t border-[#F2F3F5]">' +
        '<label class="text-xs font-medium text-fg-secondary block mb-1.5">案件来源</label>' +
        '<div class="flex gap-4">' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input checked="" class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        电话咨询' +
        '                    </label>' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        微信咨询' +
        '                    </label>' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        到所咨询' +
        '                    </label>' +
        '<label class="flex items-center gap-1.5 text-xs text-fg-secondary cursor-pointer">' +
        '<input class="accent-[#165DFF]" name="client-source" type="radio"/>' +
        '                        介绍推荐' +
        '                    </label>' +
        '</div>' +
        '</div>' +
        '<div class="pt-3 border-t border-[#F2F3F5]">' +
        '<div class="flex items-center justify-between mb-2">' +
        '<div class="flex items-center gap-1.5">' +
        '<iconify-icon class="text-sm text-brand" icon="mdi:shield-check-outline"></iconify-icon>' +
        '<span class="text-xs font-medium text-fg-primary">利益冲突检索</span>' +
        '</div>' +
        '<button class="text-[10px] text-brand hover:underline" onclick="runNewClientConflictCheck()">立即检索</button>' +
        '</div>' +
        '<div class="flex items-center gap-2 text-[10px] text-fg-tertiary">' +
        '<iconify-icon icon="mdi:information-outline"></iconify-icon>' +
        '<span>提交时将强制进行精确查重，已存在则提示是否合并</span>' +
        '</div>' +
        '<div class="hidden mt-2" id="new-client-conflict-result">' +
        '<div class="flex items-center gap-1.5 text-[10px] text-success">' +
        '<iconify-icon icon="mdi:check-circle"></iconify-icon>' +
        '<span>未发现冲突</span>' +
        '</div>' +
        '</div>' +
        '</div>' +
        '</div>';

    var footer = '<button class="px-4 py-2 text-xs font-medium rounded-lg border border-bg-border text-fg-secondary hover:bg-bg-subtle transition-colors" onclick="closeNewClientModal()">取消</button>' +
        '<button class="px-4 py-2 text-xs font-semibold rounded-lg bg-brand text-white hover:bg-brand-hover transition-colors" onclick="submitNewClient()">保存并新建</button>';

    if (_closeNewClientModal) _closeNewClientModal();
    _closeNewClientModal = Utils.showModal({
        id: 'new-client-modal',
        title: '新建客户',
        content: content,
        footer: footer,
        size: 'md'
    });
}


function closeNewClientModal() {
    if (_closeNewClientModal) {
        _closeNewClientModal();
        _closeNewClientModal = null;
    }
}


function submitNewClient() {
    showSaveSuccess('客户信息已保存，请完善案件信息');
    closeNewClientModal();
}

function runNewClientConflictCheck() {
    var result = document.getElementById('new-client-conflict-result');
    if (result) {
        result.classList.remove('hidden');
    }
    showSaveSuccess('利益冲突检索完成，未发现冲突');
}

function runConflictCheck() {
    var result = document.getElementById('conflict-result');
    if (result) {
        result.classList.remove('hidden');
    }
    showSaveSuccess('利益冲突审查完成');
}
