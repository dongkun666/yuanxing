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

    function showNewClientModal() {
        document.getElementById('new-client-modal').classList.remove('hidden');
    }


    function closeNewClientModal() {
        document.getElementById('new-client-modal').classList.add('hidden');
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
