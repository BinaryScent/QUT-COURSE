// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    initNavbar();
});

// 初始化导航栏
function initNavbar() {
    const navColleges = document.getElementById('navColleges');
    navColleges.innerHTML = qutData.colleges.map(college => `
        <li class="nav-item">
            <a href="#" class="nav-link" onclick="showGrades('${college.id}'); return false;">${college.name}</a>
            <div class="nav-dropdown">
                ${college.grades.map(grade => `
                    <a href="#" class="dropdown-item" onclick="showMajors('${college.id}', '${grade.id}'); return false;">
                        ${grade.name}
                    </a>
                `).join('')}
            </div>
        </li>
    `).join('');
}

// 显示首页
function showHome() {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('homePage').classList.add('active');
    currentCollege = null;
    currentGrade = null;
    currentMajor = null;
    currentCourse = null;
    window.scrollTo(0, 0);
}

// 显示年级页
function showGrades(collegeId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('gradePage').classList.add('active');

    // 更新面包屑
    document.getElementById('breadcrumbCollege').textContent = currentCollege.name;

    // 渲染年级
    const container = document.getElementById('gradesContainer');
    container.innerHTML = currentCollege.grades.map(grade => `
        <div class="card" onclick="showMajors('${currentCollege.id}', '${grade.id}')">
            <i class="fas fa-calendar-alt"></i>
            <h3>${grade.name}</h3>
            <p>${grade.majors.length}个专业</p>
        </div>
    `).join('');

    window.scrollTo(0, 0);
}

// 显示专业页
function showMajors(collegeId, gradeId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    currentGrade = currentCollege.grades.find(g => g.id === gradeId);
    if (!currentGrade) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('majorPage').classList.add('active');

    // 更新面包屑
    document.getElementById('breadcrumbCollege2').textContent = currentCollege.name;
    document.getElementById('breadcrumbGrade').textContent = currentGrade.name;

    // 渲染专业
    const container = document.getElementById('majorsContainer');
    container.innerHTML = currentGrade.majors.map(major => `
        <div class="card" onclick="showMajorDetail('${currentCollege.id}', '${currentGrade.id}', '${major.id}')">
            <i class="fas fa-graduation-cap"></i>
            <h3>${major.name}</h3>
            <p>${major.courses.length}门课程</p>
        </div>
    `).join('');

    window.scrollTo(0, 0);
}

// 显示专业详情
function showMajorDetail(collegeId, gradeId, majorId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    currentGrade = currentCollege.grades.find(g => g.id === gradeId);
    if (!currentGrade) return;

    currentMajor = currentGrade.majors.find(m => m.id === majorId);
    if (!currentMajor) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('majorDetailPage').classList.add('active');

    // 更新面包屑
    document.getElementById('breadcrumbCollege3').textContent = currentCollege.name;
    document.getElementById('breadcrumbGrade2').textContent = currentGrade.name;
    document.getElementById('breadcrumbMajor').textContent = currentMajor.name;

    // 渲染培养方案
    renderPlanContent();

    // 渲染课程选择
    renderCourseSelect();

    // 默认显示培养方案
    showSection('plan');

    window.scrollTo(0, 0);
}

// 渲染培养方案内容
function renderPlanContent() {
    const container = document.getElementById('planContent');
    
    if (currentMajor.planFile) {
        container.innerHTML = `
            <i class="fas fa-file-pdf plan-icon"></i>
            <h3>${currentMajor.name} 培养方案</h3>
            <p>点击下方按钮下载查看培养方案</p>
            <a href="${currentMajor.planFile}" class="btn-download" target="_blank">
                <i class="fas fa-download"></i> 下载培养方案
            </a>
        `;
    } else {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-alt"></i>
                <h3>暂无培养方案</h3>
            </div>
        `;
    }
}

// 渲染课程选择器
function renderCourseSelect() {
    const select = document.getElementById('courseSelect');
    select.innerHTML = '<option value="">-- 请选择课程 --</option>' +
        currentMajor.courses.map(course => `
            <option value="${course.id}">${course.name} (${course.type})</option>
        `).join('');

    // 清空课程资源显示
    document.getElementById('courseResources').innerHTML = `
        <div class="empty-state">
            <i class="fas fa-book"></i>
            <h3>请先选择一门课程</h3>
        </div>
    `;
}

// 显示部分（培养方案或课程资料）
function showSection(section) {
    // 更新侧边栏激活状态
    document.querySelectorAll('.sidebar-item').forEach(item => item.classList.remove('active'));
    document.querySelector(`.sidebar-item[data-section="${section}"]`).classList.add('active');

    // 更新内容显示
    document.querySelectorAll('.content-section').forEach(sec => sec.classList.remove('active'));
    document.getElementById(`${section}Section`).classList.add('active');
}

// 显示课程资源
function showCourseResources() {
    const courseId = document.getElementById('courseSelect').value;
    const container = document.getElementById('courseResources');

    if (!courseId) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-book"></i>
                <h3>请先选择一门课程</h3>
            </div>
        `;
        return;
    }

    currentCourse = currentMajor.courses.find(c => c.id === courseId);
    if (!currentCourse) return;

    container.innerHTML = `
        <div class="resource-tabs">
            <button class="tab-btn active" data-type="homeworks" onclick="showResourceType('homeworks')">
                <i class="fas fa-pencil-alt"></i> 作业
            </button>
            <button class="tab-btn" data-type="labs" onclick="showResourceType('labs')">
                <i class="fas fa-flask"></i> 实验
            </button>
            <button class="tab-btn" data-type="exams" onclick="showResourceType('exams')">
                <i class="fas fa-file-alt"></i> 考试
            </button>
            <button class="tab-btn" data-type="notes" onclick="showResourceType('notes')">
                <i class="fas fa-sticky-note"></i> 笔记
            </button>
        </div>

        <div id="homeworksTab" class="resource-tab-content active">
            ${renderResourceList('homeworks')}
        </div>
        <div id="labsTab" class="resource-tab-content">
            ${renderResourceList('labs')}
        </div>
        <div id="examsTab" class="resource-tab-content">
            ${renderResourceList('exams')}
        </div>
        <div id="notesTab" class="resource-tab-content">
            ${renderResourceList('notes')}
        </div>
    `;
}

// 显示资源类型
function showResourceType(type) {
    // 更新按钮激活状态
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.tab-btn[data-type="${type}"]`).classList.add('active');

    // 更新内容显示
    document.querySelectorAll('.resource-tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`${type}Tab`).classList.add('active');
}

// 渲染资源列表
function renderResourceList(type) {
    const resources = currentCourse.resources[type];

    if (resources.length === 0) {
        return `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>暂无资源</h3>
            </div>
        `;
    }

    return `
        <div class="resource-list">
            ${resources.map(resource => `
                <div class="resource-item">
                    <i class="${getResourceIcon(resource.name)}"></i>
                    <div class="resource-info">
                        <h4>${resource.name}</h4>
                        <p>${resource.description || '暂无描述'}</p>
                    </div>
                    <a href="${resource.url}" class="download-btn" target="_blank">
                        <i class="fas fa-download"></i> 下载
                    </a>
                </div>
            `).join('')}
        </div>
    `;
}

// 获取资源图标
function getResourceIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const iconMap = {
        pdf: 'fas fa-file-pdf',
        doc: 'fas fa-file-word',
        docx: 'fas fa-file-word',
        ppt: 'fas fa-file-powerpoint',
        pptx: 'fas fa-file-powerpoint',
        xls: 'fas fa-file-excel',
        xlsx: 'fas fa-file-excel',
        jpg: 'fas fa-file-image',
        jpeg: 'fas fa-file-image',
        png: 'fas fa-file-image',
        gif: 'fas fa-file-image',
        zip: 'fas fa-file-archive',
        rar: 'fas fa-file-archive',
        '7z': 'fas fa-file-archive',
        py: 'fas fa-file-code',
        java: 'fas fa-file-code',
        cpp: 'fas fa-file-code',
        c: 'fas fa-file-code',
        js: 'fas fa-file-code',
        html: 'fas fa-file-code',
        css: 'fas fa-file-code'
    };
    return iconMap[ext] || 'fas fa-file';
}
