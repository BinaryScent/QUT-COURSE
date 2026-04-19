let currentCollege = null;
let currentMajor = null;
let currentGrade = null;
let currentCourse = null;

document.addEventListener('DOMContentLoaded', function() {
    initNavbar();
});

function initNavbar() {
    const navColleges = document.getElementById('navColleges');
    navColleges.innerHTML = qutData.colleges.map(college => `
        <li class="nav-item">
            <a href="#" class="nav-link" onclick="showCollegePage('${college.id}'); return false;">${college.name}</a>
        </li>
    `).join('');
}

function showHome() {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('homePage').classList.add('active');
    currentCollege = null;
    currentMajor = null;
    currentGrade = null;
    currentCourse = null;
    window.scrollTo(0, 0);
}

function showCollegePage(collegeId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('collegePage').classList.add('active');
    document.getElementById('breadcrumbCollege').textContent = currentCollege.name;

    window.scrollTo(0, 0);
}

function showMajorListForPlan(collegeId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('majorListPage').classList.add('active');
    document.getElementById('breadcrumbCollege2').textContent = currentCollege.name;

    const container = document.getElementById('majorListContainer');
    if (currentCollege.majors.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><h3>暂无专业数据</h3></div>';
        return;
    }

    container.innerHTML = currentCollege.majors.map(major => `
        <div class="card" onclick="showGradeListForPlan('${currentCollege.id}', '${major.id}')">
            <i class="fas fa-graduation-cap"></i>
            <h3>${major.name}</h3>
            <p>${major.plans.length}个年级培养方案</p>
        </div>
    `).join('');

    window.scrollTo(0, 0);
}

function showGradeListForPlan(collegeId, majorId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    currentMajor = currentCollege.majors.find(m => m.id === majorId);
    if (!currentMajor) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('gradeListPage').classList.add('active');
    document.getElementById('breadcrumbCollege3').textContent = currentCollege.name;
    document.getElementById('breadcrumbMajor').textContent = currentMajor.name;

    const container = document.getElementById('gradeListContainer');
    if (currentMajor.plans.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><h3>暂无培养方案</h3></div>';
        return;
    }

    container.innerHTML = currentMajor.plans.map(plan => `
        <div class="card" onclick="showPlanDownload('${currentCollege.id}', '${currentMajor.id}', '${plan.grade}')">
            <i class="fas fa-calendar-alt"></i>
            <h3>${plan.grade}</h3>
            <p>点击查看培养方案</p>
        </div>
    `).join('');

    window.scrollTo(0, 0);
}

function showPlanDownload(collegeId, majorId, grade) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    currentMajor = currentCollege.majors.find(m => m.id === majorId);
    if (!currentMajor) return;

    const plan = currentMajor.plans.find(p => p.grade === grade);
    if (!plan) return;

    currentGrade = { id: grade };

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('planDownloadPage').classList.add('active');
    document.getElementById('breadcrumbCollege4').textContent = currentCollege.name;
    document.getElementById('breadcrumbMajor2').textContent = currentMajor.name;
    document.getElementById('breadcrumbGrade').textContent = grade;

    const container = document.getElementById('planDownloadContent');
    container.innerHTML = `
        <i class="fas fa-file-pdf plan-icon"></i>
        <h3>${currentMajor.name} ${grade} 培养方案</h3>
        <p>点击下方按钮下载查看培养方案</p>
        <a href="${plan.file}" class="btn-download" target="_blank">
            <i class="fas fa-download"></i> 下载培养方案
        </a>
    `;

    window.scrollTo(0, 0);
}

function showCourseList(collegeId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('courseListPage').classList.add('active');
    document.getElementById('breadcrumbCollege5').textContent = currentCollege.name;

    const filterSelect = document.getElementById('courseTypeFilter');
    const courseTypes = [...new Set(currentCollege.courses.map(c => c.type))];
    filterSelect.innerHTML = '<option value="">全部类型</option>' + 
        courseTypes.map(type => `<option value="${type}">${type}</option>`).join('');

    renderCourseList(currentCollege.courses);

    window.scrollTo(0, 0);
}

function renderCourseList(courses) {
    const container = document.getElementById('courseListContainer');
    if (courses.length === 0) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><h3>暂无课程</h3></div>';
        return;
    }

    container.innerHTML = courses.map(course => `
        <div class="card" onclick="showCourseDetail('${currentCollege.id}', '${course.id}')">
            <i class="fas fa-book"></i>
            <h3>${course.name}</h3>
            <p>${course.type}</p>
        </div>
    `).join('');
}

function filterCoursesByType() {
    const type = document.getElementById('courseTypeFilter').value;
    if (!type) {
        renderCourseList(currentCollege.courses);
    } else {
        const filtered = currentCollege.courses.filter(c => c.type === type);
        renderCourseList(filtered);
    }
}

function showCourseDetail(collegeId, courseId) {
    currentCollege = qutData.colleges.find(c => c.id === collegeId);
    if (!currentCollege) return;

    currentCourse = currentCollege.courses.find(c => c.id === courseId);
    if (!currentCourse) return;

    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById('courseDetailPage').classList.add('active');
    document.getElementById('breadcrumbCollege6').textContent = currentCollege.name;
    document.getElementById('breadcrumbCourse').textContent = currentCourse.name;
    document.getElementById('courseDetailTitle').textContent = currentCourse.name;

    renderResourceTab('homeworks');
    renderResourceTab('labs');
    renderResourceTab('exams');
    renderResourceTab('notes');

    showResourceType('homeworks');

    window.scrollTo(0, 0);
}

function renderResourceTab(type) {
    const resources = currentCourse.resources[type] || [];
    const container = document.getElementById(`${type}Content`);

    if (resources.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>暂无资源</h3>
            </div>
        `;
        return;
    }

    container.innerHTML = `
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

function showResourceType(type) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.tab-btn[data-type="${type}"]`).classList.add('active');

    document.querySelectorAll('.resource-tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`${type}Tab`).classList.add('active');
}

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
