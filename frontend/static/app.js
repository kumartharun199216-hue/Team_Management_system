const API_BASE = '/api/v1';

let state = {
  token: localStorage.getItem('token') || '',
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  currentView: 'dashboard',
  projects: [],
  tasks: [],
  users: [],
  stats: null,
  activities: [],
  taskFilter: {
    search: '',
    status: '',
    priority: '',
    projectId: '',
    assignedToMe: false,
    sortBy: 'created_at',
    sortOrder: 'desc'
  },
  projectFilter: {
    search: '',
    status: ''
  }
};

document.addEventListener('DOMContentLoaded', async () => {
  if (!state.token) {
    await performLogin('admin@example.com', 'admin123');
  } else {
    try {
      await fetchCurrentUser();
    } catch (e) {
      await performLogin('admin@example.com', 'admin123');
    }
  }
  updateSidebarUser();
  await loadGlobalData();
  navigate('dashboard');
});

async function apiRequest(endpoint, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  const options = { method, headers };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(`${API_BASE}${endpoint}`, options);
  if (res.status === 401) {
    showLoginModal();
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    let errDetail = 'Request failed';
    try {
      const errJson = await res.json();
      errDetail = errJson.detail || JSON.stringify(errJson);
    } catch (_) {}
    throw new Error(errDetail);
  }
  if (res.status === 204) return null;
  return await res.json();
}

async function fetchCurrentUser() {
  const user = await apiRequest('/auth/me');
  state.user = user;
  localStorage.setItem('user', JSON.stringify(user));
  updateSidebarUser();
}

async function performLogin(email, password) {
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error('Invalid credentials');
    const data = await res.json();
    state.token = data.access_token;
    state.user = data.user;
    localStorage.setItem('token', state.token);
    localStorage.setItem('user', JSON.stringify(state.user));
    closeModal('modal-login');
    updateSidebarUser();
    return true;
  } catch (err) {
    console.error('Login error:', err);
    return false;
  }
}

async function quickSwitchUser(combo) {
  const [email, password] = combo.split(':');
  const success = await performLogin(email, password);
  if (success) {
    await loadGlobalData();
    navigate(state.currentView);
  }
}

function logout() {
  state.token = '';
  state.user = null;
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  showLoginModal();
}

function showLoginModal() {
  document.getElementById('modal-login').classList.add('active');
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const pass = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  const success = await performLogin(email, pass);
  if (!success) {
    errEl.textContent = 'Invalid email or password.';
  } else {
    await loadGlobalData();
    navigate(state.currentView);
  }
}

function updateSidebarUser() {
  if (!state.user) return;
  document.getElementById('sidebar-user-name').textContent = state.user.full_name;
  document.getElementById('sidebar-user-role').textContent = state.user.role;
  document.getElementById('sidebar-avatar').textContent = state.user.full_name.charAt(0).toUpperCase();

  const select = document.getElementById('quick-role-select');
  if (select) {
    for (let opt of select.options) {
      if (opt.value.startsWith(state.user.email)) {
        opt.selected = true;
        break;
      }
    }
  }
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

async function loadGlobalData() {
  try {
    const [stats, projects, tasks, users] = await Promise.all([
      apiRequest('/dashboard/stats'),
      apiRequest('/projects'),
      apiRequest('/tasks'),
      apiRequest('/users')
    ]);
    state.stats = stats;
    state.projects = projects;
    state.tasks = tasks;
    state.users = users;

    document.getElementById('badge-projects').textContent = projects.length;
    document.getElementById('badge-tasks').textContent = tasks.length;
  } catch (err) {
    console.error('Failed to load global data', err);
  }
}

function navigate(view) {
  state.currentView = view;
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.view === view);
  });

  const titles = {
    dashboard: 'Dashboard Overview',
    projects: 'Project Management',
    tasks: 'Task Management',
    team: 'Team & User Management',
    activity: 'Audit & Activity Logs'
  };
  document.getElementById('view-title').textContent = titles[view] || 'ApexPlan Pro';

  const container = document.getElementById('content-area');
  if (view === 'dashboard') renderDashboardView(container);
  else if (view === 'projects') renderProjectsView(container);
  else if (view === 'tasks') renderTasksView(container);
  else if (view === 'team') renderTeamView(container);
  else if (view === 'activity') renderActivityView(container);

  document.getElementById('sidebar').classList.remove('open');
}

function renderDashboardView(container) {
  const s = state.stats || {
    total_projects: 0,
    total_tasks: 0,
    completed_tasks: 0,
    pending_tasks: 0,
    in_progress_tasks: 0,
    completion_rate: 0,
    total_users: 0,
    recent_activities: []
  };

  container.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon blue"><i class="fa-solid fa-folder-tree"></i></div>
        <div class="stat-info">
          <h3>${s.total_projects}</h3>
          <p>Total Projects</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon purple"><i class="fa-solid fa-list-check"></i></div>
        <div class="stat-info">
          <h3>${s.total_tasks}</h3>
          <p>Total Tasks</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green"><i class="fa-solid fa-circle-check"></i></div>
        <div class="stat-info">
          <h3>${s.completed_tasks}</h3>
          <p>Completed Tasks (${s.completion_rate}%)</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon yellow"><i class="fa-solid fa-hourglass-half"></i></div>
        <div class="stat-info">
          <h3>${s.in_progress_tasks}</h3>
          <p>In-Progress Tasks</p>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 24px;">
      <div class="card">
        <div class="section-header">
          <h2>Project Progress</h2>
          <button class="btn btn-outline btn-sm" onclick="navigate('projects')">View All</button>
        </div>
        <div style="display: flex; flex-direction: column; gap: 18px;">
          ${state.projects.map(p => {
            const pct = p.progress ? p.progress.progress_percentage : 0;
            return `
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.875rem; margin-bottom: 4px;">
                  <span style="font-weight: 600;">${escapeHtml(p.name)}</span>
                  <span style="font-weight: 600; color: var(--primary);">${pct}%</span>
                </div>
                <div class="progress-bar-container">
                  <div class="progress-bar-fill" style="width: ${pct}%;"></div>
                </div>
                <div style="display: flex; gap: 12px; font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">
                  <span>Status: <b>${p.status}</b></span>
                  <span>Tasks: <b>${p.progress ? p.progress.total_tasks : 0}</b></span>
                  <span>Team: <b>${p.members ? p.members.length : 0} members</b></span>
                </div>
              </div>
            `;
          }).join('')}
          ${state.projects.length === 0 ? '<p style="color: var(--text-muted); font-size: 0.85rem;">No projects found.</p>' : ''}
        </div>
      </div>

      <div class="card">
        <div class="section-header">
          <h2>Recent Activity History</h2>
          <button class="btn btn-outline btn-sm" onclick="navigate('activity')">All Logs</button>
        </div>
        <div class="activity-list">
          ${(s.recent_activities || []).slice(0, 7).map(act => `
            <div class="activity-item">
              <div class="activity-bullet"></div>
              <div class="activity-content">
                <div class="activity-title">${escapeHtml(act.action)}</div>
                <div class="activity-details">${escapeHtml(act.details || '')}</div>
                <div class="activity-time">${formatDate(act.timestamp)} by <b>${act.user ? escapeHtml(act.user.full_name) : 'User'}</b></div>
              </div>
            </div>
          `).join('')}
          ${(!s.recent_activities || s.recent_activities.length === 0) ? '<p style="color: var(--text-muted); font-size: 0.85rem;">No recent activities.</p>' : ''}
        </div>
      </div>
    </div>
  `;
}

function renderProjectsView(container) {
  const canManage = state.user && (state.user.role === 'Admin' || state.user.role === 'Project Manager');

  let filtered = state.projects.filter(p => {
    if (state.projectFilter.search) {
      const q = state.projectFilter.search.toLowerCase();
      if (!p.name.toLowerCase().includes(q) && !(p.description || '').toLowerCase().includes(q)) return false;
    }
    if (state.projectFilter.status && p.status !== state.projectFilter.status) return false;
    return true;
  });

  container.innerHTML = `
    <div class="section-header">
      <div>
        <p style="color: var(--text-muted); font-size: 0.875rem;">Manage company projects, member assignments, and monitor milestones.</p>
      </div>
      ${canManage ? `<button class="btn btn-primary" onclick="openProjectModal()"><i class="fa-solid fa-plus"></i> New Project</button>` : ''}
    </div>

    <div class="filter-bar">
      <input type="text" class="search-input" placeholder="Search projects by title or description..."
        value="${escapeHtml(state.projectFilter.search)}"
        oninput="state.projectFilter.search = this.value; renderProjectsView(document.getElementById('content-area'))">

      <select class="filter-select" onchange="state.projectFilter.status = this.value; renderProjectsView(document.getElementById('content-area'))">
        <option value="">All Project Statuses</option>
        <option value="Planning" ${state.projectFilter.status === 'Planning' ? 'selected' : ''}>Planning</option>
        <option value="In Progress" ${state.projectFilter.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
        <option value="On Hold" ${state.projectFilter.status === 'On Hold' ? 'selected' : ''}>On Hold</option>
        <option value="Completed" ${state.projectFilter.status === 'Completed' ? 'selected' : ''}>Completed</option>
        <option value="Cancelled" ${state.projectFilter.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
      </select>
    </div>

    <div class="card" style="padding: 0;">
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Project</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Start / End Date</th>
              <th>Members</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(p => {
              const pct = p.progress ? p.progress.progress_percentage : 0;
              const isOwnerOrAdmin = state.user && (state.user.role === 'Admin' || p.owner_id === state.user.id);

              return `
                <tr>
                  <td>
                    <div style="font-weight: 600; color: var(--text-main); font-size: 0.95rem;">${escapeHtml(p.name)}</div>
                    <div style="color: var(--text-muted); font-size: 0.8rem; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                      ${escapeHtml(p.description || 'No description provided')}
                    </div>
                  </td>
                  <td><span class="badge badge-inprogress">${p.status}</span></td>
                  <td style="min-width: 140px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 600; margin-bottom: 2px;">
                      <span>${p.progress ? p.progress.completed_tasks : 0}/${p.progress ? p.progress.total_tasks : 0} Done</span>
                      <span>${pct}%</span>
                    </div>
                    <div class="progress-bar-container">
                      <div class="progress-bar-fill" style="width: ${pct}%;"></div>
                    </div>
                  </td>
                  <td style="font-size: 0.8rem; color: var(--text-muted);">
                    <div><i class="fa-regular fa-calendar-check"></i> ${p.start_date ? formatDateOnly(p.start_date) : 'N/A'}</div>
                    <div><i class="fa-regular fa-calendar-xmark"></i> ${p.end_date ? formatDateOnly(p.end_date) : 'N/A'}</div>
                  </td>
                  <td>
                    <div style="display: flex; gap: -4px; align-items: center;">
                      <span style="font-size: 0.8rem; font-weight: 500;">${(p.members || []).length} assigned</span>
                      ${isOwnerOrAdmin ? `
                        <button class="btn btn-outline btn-sm" style="margin-left: 8px; padding: 2px 6px;" onclick="openAssignMembersModal(${p.id})">
                          <i class="fa-solid fa-user-plus"></i>
                        </button>
                      ` : ''}
                    </div>
                  </td>
                  <td style="text-align: right;">
                    ${isOwnerOrAdmin ? `
                      <button class="btn btn-outline btn-sm" onclick="openEditProjectModal(${p.id})"><i class="fa-solid fa-pen"></i></button>
                      <button class="btn btn-danger btn-sm" onclick="handleDeleteProject(${p.id})"><i class="fa-solid fa-trash"></i></button>
                    ` : `<span style="font-size: 0.75rem; color: var(--text-muted);">View Only</span>`}
                  </td>
                </tr>
              `;
            }).join('')}
            ${filtered.length === 0 ? '<tr><td colspan="6" style="text-align:center; padding: 32px; color: var(--text-muted);">No projects match criteria.</td></tr>' : ''}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderTasksView(container) {
  let filtered = state.tasks.filter(t => {
    if (state.taskFilter.search) {
      const q = state.taskFilter.search.toLowerCase();
      if (!t.title.toLowerCase().includes(q) && !(t.description || '').toLowerCase().includes(q)) return false;
    }
    if (state.taskFilter.status && t.status !== state.taskFilter.status) return false;
    if (state.taskFilter.priority && t.priority !== state.taskFilter.priority) return false;
    if (state.taskFilter.projectId && String(t.project_id) !== String(state.taskFilter.projectId)) return false;
    if (state.taskFilter.assignedToMe && state.user && t.assignee_id !== state.user.id) return false;
    return true;
  });

  filtered.sort((a, b) => {
    let fieldA = a[state.taskFilter.sortBy] || '';
    let fieldB = b[state.taskFilter.sortBy] || '';
    if (state.taskFilter.sortOrder === 'asc') return fieldA > fieldB ? 1 : -1;
    return fieldA < fieldB ? 1 : -1;
  });

  container.innerHTML = `
    <div class="section-header">
      <div>
        <p style="color: var(--text-muted); font-size: 0.875rem;">Create, track, prioritize, and collaborate on project tasks.</p>
      </div>
      <button class="btn btn-primary" onclick="openTaskModal()"><i class="fa-solid fa-plus"></i> New Task</button>
    </div>

    <div class="filter-bar">
      <input type="text" class="search-input" placeholder="Search tasks..."
        value="${escapeHtml(state.taskFilter.search)}"
        oninput="state.taskFilter.search = this.value; renderTasksView(document.getElementById('content-area'))">

      <select class="filter-select" onchange="state.taskFilter.projectId = this.value; renderTasksView(document.getElementById('content-area'))">
        <option value="">All Projects</option>
        ${state.projects.map(p => `
          <option value="${p.id}" ${String(state.taskFilter.projectId) === String(p.id) ? 'selected' : ''}>${escapeHtml(p.name)}</option>
        `).join('')}
      </select>

      <select class="filter-select" onchange="state.taskFilter.status = this.value; renderTasksView(document.getElementById('content-area'))">
        <option value="">All Statuses</option>
        <option value="To Do" ${state.taskFilter.status === 'To Do' ? 'selected' : ''}>To Do</option>
        <option value="In Progress" ${state.taskFilter.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
        <option value="Review" ${state.taskFilter.status === 'Review' ? 'selected' : ''}>Review</option>
        <option value="Completed" ${state.taskFilter.status === 'Completed' ? 'selected' : ''}>Completed</option>
      </select>

      <select class="filter-select" onchange="state.taskFilter.priority = this.value; renderTasksView(document.getElementById('content-area'))">
        <option value="">All Priorities</option>
        <option value="Low" ${state.taskFilter.priority === 'Low' ? 'selected' : ''}>Low</option>
        <option value="Medium" ${state.taskFilter.priority === 'Medium' ? 'selected' : ''}>Medium</option>
        <option value="High" ${state.taskFilter.priority === 'High' ? 'selected' : ''}>High</option>
        <option value="Critical" ${state.taskFilter.priority === 'Critical' ? 'selected' : ''}>Critical</option>
      </select>

      <select class="filter-select" onchange="state.taskFilter.sortBy = this.value; renderTasksView(document.getElementById('content-area'))">
        <option value="created_at" ${state.taskFilter.sortBy === 'created_at' ? 'selected' : ''}>Sort by Date Created</option>
        <option value="deadline" ${state.taskFilter.sortBy === 'deadline' ? 'selected' : ''}>Sort by Deadline</option>
      </select>

      <button class="btn ${state.taskFilter.assignedToMe ? 'btn-primary' : 'btn-outline'} btn-sm"
        onclick="state.taskFilter.assignedToMe = !state.taskFilter.assignedToMe; renderTasksView(document.getElementById('content-area'))">
        <i class="fa-solid fa-user-tag"></i> Assigned to Me
      </button>
    </div>

    <div class="card" style="padding: 0;">
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Project</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Assignee</th>
              <th>Deadline</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map(t => {
              const proj = state.projects.find(p => p.id === t.project_id);
              const priorityClass = t.priority.toLowerCase();

              return `
                <tr>
                  <td>
                    <a href="javascript:void(0)" onclick="openTaskDrawer(${t.id})" style="font-weight: 600; color: var(--primary); text-decoration: none; font-size: 0.95rem;">
                      ${escapeHtml(t.title)}
                    </a>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${(t.comments || []).length} comments</div>
                  </td>
                  <td><span style="font-size: 0.85rem; font-weight: 500;">${proj ? escapeHtml(proj.name) : 'Unknown'}</span></td>
                  <td>
                    <select class="form-control" style="width: auto; padding: 4px 8px; font-size: 0.8rem; font-weight: 500;"
                      onchange="quickUpdateTaskStatus(${t.id}, this.value)">
                      <option value="To Do" ${t.status === 'To Do' ? 'selected' : ''}>To Do</option>
                      <option value="In Progress" ${t.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                      <option value="Review" ${t.status === 'Review' ? 'selected' : ''}>Review</option>
                      <option value="Completed" ${t.status === 'Completed' ? 'selected' : ''}>Completed</option>
                    </select>
                  </td>
                  <td><span class="badge badge-${priorityClass}">${t.priority}</span></td>
                  <td><span style="font-size: 0.85rem;">${t.assignee ? escapeHtml(t.assignee.full_name) : '<em style="color:var(--text-sub)">Unassigned</em>'}</span></td>
                  <td style="font-size: 0.85rem;">
                    ${t.deadline ? `<span style="${new Date(t.deadline) < new Date() && t.status !== 'Completed' ? 'color: var(--danger); font-weight: 600;' : ''}">${formatDateOnly(t.deadline)}</span>` : '<span style="color:var(--text-sub)">None</span>'}
                  </td>
                  <td style="text-align: right;">
                    <button class="btn btn-outline btn-sm" onclick="openTaskDrawer(${t.id})" title="Details & Comments"><i class="fa-solid fa-comment-dots"></i></button>
                    <button class="btn btn-outline btn-sm" onclick="openEditTaskModal(${t.id})" title="Edit"><i class="fa-solid fa-pen"></i></button>
                    <button class="btn btn-danger btn-sm" onclick="handleDeleteTask(${t.id})" title="Delete"><i class="fa-solid fa-trash"></i></button>
                  </td>
                </tr>
              `;
            }).join('')}
            ${filtered.length === 0 ? '<tr><td colspan="7" style="text-align:center; padding: 32px; color: var(--text-muted);">No tasks match criteria.</td></tr>' : ''}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderTeamView(container) {
  const isAdmin = state.user && state.user.role === 'Admin';

  container.innerHTML = `
    <div class="section-header">
      <div>
        <p style="color: var(--text-muted); font-size: 0.875rem;">Manage company members, assign RBAC access roles, and monitor activation status.</p>
      </div>
      ${isAdmin ? `<button class="btn btn-primary" onclick="openUserModal()"><i class="fa-solid fa-user-plus"></i> Add New User</button>` : ''}
    </div>

    <div class="card" style="padding: 0;">
      <div class="table-responsive">
        <table class="custom-table">
          <thead>
            <tr>
              <th>Member Name</th>
              <th>Email Address</th>
              <th>Role</th>
              <th>Account Status</th>
              <th>Created</th>
              <th style="text-align: right;">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${state.users.map(u => {
              const roleBadgeClass = u.role === 'Admin' ? 'badge-role-admin' : (u.role === 'Project Manager' ? 'badge-role-pm' : 'badge-role-member');
              return `
                <tr>
                  <td><div style="font-weight: 600; color: var(--text-main); font-size: 0.95rem;">${escapeHtml(u.full_name)}</div></td>
                  <td>${escapeHtml(u.email)}</td>
                  <td><span class="badge ${roleBadgeClass}">${u.role}</span></td>
                  <td><span class="badge ${u.is_active ? 'badge-completed' : 'badge-critical'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
                  <td style="font-size: 0.8rem; color: var(--text-muted);">${formatDateOnly(u.created_at)}</td>
                  <td style="text-align: right;">
                    ${isAdmin ? `
                      <button class="btn btn-outline btn-sm" onclick="openEditUserModal(${u.id})"><i class="fa-solid fa-pen"></i> Edit</button>
                      ${u.id !== state.user.id ? `
                        <button class="btn ${u.is_active ? 'btn-danger' : 'btn-outline'} btn-sm" onclick="toggleUserActive(${u.id}, ${!u.is_active})">
                          ${u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      ` : ''}
                    ` : `<span style="font-size: 0.75rem; color: var(--text-muted);">View Only</span>`}
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function renderActivityView(container) {
  try {
    const logs = await apiRequest('/activities?limit=50');
    container.innerHTML = `
      <div class="section-header">
        <div>
          <p style="color: var(--text-muted); font-size: 0.875rem;">Complete audit log stream tracking all project updates, tasks, assignments, and comments.</p>
        </div>
      </div>

      <div class="card">
        <div class="activity-list">
          ${logs.map(act => `
            <div class="activity-item">
              <div class="activity-bullet"></div>
              <div class="activity-content">
                <div class="activity-title">${escapeHtml(act.action)}</div>
                <div class="activity-details">${escapeHtml(act.details || '')}</div>
                <div class="activity-time">
                  ${formatDate(act.timestamp)} by <b>${act.user ? escapeHtml(act.user.full_name) : 'User'}</b>
                </div>
              </div>
            </div>
          `).join('')}
          ${logs.length === 0 ? '<p style="color: var(--text-muted);">No activity records found.</p>' : ''}
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="card"><p style="color:var(--danger)">Error loading activities: ${err.message}</p></div>`;
  }
}

function openProjectModal() {
  document.getElementById('modal-project-title').textContent = 'Create New Project';
  document.getElementById('project-form').reset();
  document.getElementById('project-id').value = '';
  document.getElementById('modal-project').classList.add('active');
}

function openEditProjectModal(id) {
  const p = state.projects.find(item => item.id === id);
  if (!p) return;
  document.getElementById('modal-project-title').textContent = 'Edit Project';
  document.getElementById('project-id').value = p.id;
  document.getElementById('proj-name').value = p.name;
  document.getElementById('proj-desc').value = p.description || '';
  document.getElementById('proj-status').value = p.status;
  document.getElementById('proj-start').value = p.start_date ? p.start_date.substring(0, 10) : '';
  document.getElementById('proj-end').value = p.end_date ? p.end_date.substring(0, 10) : '';
  document.getElementById('modal-project').classList.add('active');
}

async function handleSaveProject(e) {
  e.preventDefault();
  const id = document.getElementById('project-id').value;
  const name = document.getElementById('proj-name').value;
  const description = document.getElementById('proj-desc').value;
  const statusVal = document.getElementById('proj-status').value;
  const startDate = document.getElementById('proj-start').value || null;
  const endDate = document.getElementById('proj-end').value || null;

  const payload = {
    name,
    description,
    status: statusVal,
    start_date: startDate ? new Date(startDate).toISOString() : null,
    end_date: endDate ? new Date(endDate).toISOString() : null
  };

  try {
    if (id) {
      await apiRequest(`/projects/${id}`, 'PUT', payload);
    } else {
      await apiRequest('/projects', 'POST', payload);
    }
    closeModal('modal-project');
    await loadGlobalData();
    navigate('projects');
  } catch (err) {
    alert(`Error saving project: ${err.message}`);
  }
}

async function handleDeleteProject(id) {
  if (!confirm('Are you sure you want to delete this project?')) return;
  try {
    await apiRequest(`/projects/${id}`, 'DELETE');
    await loadGlobalData();
    navigate('projects');
  } catch (err) {
    alert(`Failed to delete project: ${err.message}`);
  }
}

function openAssignMembersModal(projectId) {
  const project = state.projects.find(p => p.id === projectId);
  if (!project) return;
  document.getElementById('assign-proj-id').value = projectId;
  const currentMemberIds = new Set((project.members || []).map(m => m.id));

  const listContainer = document.getElementById('assign-members-checklist');
  listContainer.innerHTML = state.users.map(u => `
    <label style="display: flex; align-items: center; gap: 10px; padding: 6px 8px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer;">
      <input type="checkbox" name="assign_user_check" value="${u.id}" ${currentMemberIds.has(u.id) ? 'checked' : ''}>
      <span style="font-weight: 500;">${escapeHtml(u.full_name)}</span>
      <span style="font-size: 0.75rem; color: var(--text-muted);">(${u.role})</span>
    </label>
  `).join('');
  document.getElementById('modal-assign-members').classList.add('active');
}

async function handleSaveProjectMembers(e) {
  e.preventDefault();
  const projectId = document.getElementById('assign-proj-id').value;
  const checked = document.querySelectorAll('input[name="assign_user_check"]:checked');
  const user_ids = Array.from(checked).map(c => parseInt(c.value));

  try {
    await apiRequest(`/projects/${projectId}/members`, 'POST', { user_ids });
    closeModal('modal-assign-members');
    await loadGlobalData();
    navigate('projects');
  } catch (err) {
    alert(`Error updating project members: ${err.message}`);
  }
}

function populateTaskModalDropdowns() {
  const projSelect = document.getElementById('task-project');
  projSelect.innerHTML = state.projects.map(p => `
    <option value="${p.id}">${escapeHtml(p.name)}</option>
  `).join('');

  const assigneeSelect = document.getElementById('task-assignee');
  assigneeSelect.innerHTML = `<option value="">Unassigned</option>` + state.users.map(u => `
    <option value="${u.id}">${escapeHtml(u.full_name)} (${u.role})</option>
  `).join('');
}

function openTaskModal() {
  populateTaskModalDropdowns();
  document.getElementById('modal-task-title').textContent = 'Create New Task';
  document.getElementById('task-form').reset();
  document.getElementById('task-id').value = '';
  document.getElementById('modal-task').classList.add('active');
}

function openEditTaskModal(id) {
  const t = state.tasks.find(item => item.id === id);
  if (!t) return;
  populateTaskModalDropdowns();
  document.getElementById('modal-task-title').textContent = 'Edit Task';
  document.getElementById('task-id').value = t.id;
  document.getElementById('task-title').value = t.title;
  document.getElementById('task-desc').value = t.description || '';
  document.getElementById('task-project').value = t.project_id;
  document.getElementById('task-status').value = t.status;
  document.getElementById('task-priority').value = t.priority;
  document.getElementById('task-assignee').value = t.assignee_id || '';
  document.getElementById('task-deadline').value = t.deadline ? t.deadline.substring(0, 10) : '';
  document.getElementById('modal-task').classList.add('active');
}

async function handleSaveTask(e) {
  e.preventDefault();
  const id = document.getElementById('task-id').value;
  const title = document.getElementById('task-title').value;
  const description = document.getElementById('task-desc').value;
  const projectId = parseInt(document.getElementById('task-project').value);
  const statusVal = document.getElementById('task-status').value;
  const priority = document.getElementById('task-priority').value;
  const assigneeId = document.getElementById('task-assignee').value ? parseInt(document.getElementById('task-assignee').value) : null;
  const deadline = document.getElementById('task-deadline').value || null;

  const payload = {
    title,
    description,
    project_id: projectId,
    status: statusVal,
    priority,
    assignee_id: assigneeId,
    deadline: deadline ? new Date(deadline).toISOString() : null
  };

  try {
    if (id) {
      await apiRequest(`/tasks/${id}`, 'PUT', payload);
    } else {
      await apiRequest('/tasks', 'POST', payload);
    }
    closeModal('modal-task');
    await loadGlobalData();
    navigate('tasks');
  } catch (err) {
    alert(`Error saving task: ${err.message}`);
  }
}

async function quickUpdateTaskStatus(taskId, newStatus) {
  try {
    await apiRequest(`/tasks/${taskId}`, 'PUT', { status: newStatus });
    await loadGlobalData();
    navigate('tasks');
  } catch (err) {
    alert(`Could not update status: ${err.message}`);
  }
}

async function handleDeleteTask(id) {
  if (!confirm('Are you sure you want to delete this task?')) return;
  try {
    await apiRequest(`/tasks/${id}`, 'DELETE');
    await loadGlobalData();
    navigate('tasks');
  } catch (err) {
    alert(`Failed to delete task: ${err.message}`);
  }
}

async function openTaskDrawer(taskId) {
  try {
    const task = await apiRequest(`/tasks/${taskId}`);
    const proj = state.projects.find(p => p.id === task.project_id);

    document.getElementById('drawer-task-title').textContent = task.title;
    const drawerBody = document.getElementById('drawer-body');
    drawerBody.innerHTML = `
      <div style="margin-bottom: 16px;">
        <span class="badge badge-${task.priority.toLowerCase()}">${task.priority} Priority</span>
        <span class="badge badge-inprogress" style="margin-left: 6px;">${task.status}</span>
      </div>

      <p style="font-size: 0.9rem; color: #334155; margin-bottom: 20px; line-height: 1.6;">
        ${escapeHtml(task.description || 'No description provided.')}
      </p>

      <div style="background-color: #f8fafc; padding: 14px; border-radius: var(--radius-sm); margin-bottom: 20px; font-size: 0.85rem; display: flex; flex-direction: column; gap: 8px;">
        <div><b>Project:</b> ${proj ? escapeHtml(proj.name) : 'N/A'}</div>
        <div><b>Assignee:</b> ${task.assignee ? escapeHtml(task.assignee.full_name) : 'Unassigned'}</div>
        <div><b>Created By:</b> ${task.creator ? escapeHtml(task.creator.full_name) : 'User'}</div>
        <div><b>Deadline:</b> ${task.deadline ? formatDateOnly(task.deadline) : 'No deadline'}</div>
      </div>

      <div class="comment-box">
        <h4 style="font-size: 0.95rem; margin-bottom: 12px;">Comments (${(task.comments || []).length})</h4>
        <div id="drawer-comments-list">
          ${(task.comments || []).map(c => `
            <div class="comment-item">
              <div class="comment-author">
                <span>${c.author ? escapeHtml(c.author.full_name) : 'Member'}</span>
                <span style="font-size: 0.75rem; color: var(--text-sub);">${formatDate(c.created_at)}</span>
              </div>
              <div class="comment-text">${escapeHtml(c.content)}</div>
            </div>
          `).join('')}
          ${(!task.comments || task.comments.length === 0) ? '<p style="color:var(--text-muted); font-size: 0.85rem;">No comments yet.</p>' : ''}
        </div>

        <form onsubmit="handleSendComment(event, ${task.id})" style="margin-top: 16px;">
          <textarea id="drawer-new-comment" class="form-control" placeholder="Write a comment..." required style="min-height: 60px;"></textarea>
          <button type="submit" class="btn btn-primary btn-sm" style="margin-top: 8px;">Post Comment</button>
        </form>
      </div>
    `;

    document.getElementById('drawer-overlay').classList.add('active');
    document.getElementById('task-drawer').classList.add('active');
  } catch (err) {
    alert(`Could not load task details: ${err.message}`);
  }
}

function closeTaskDrawer() {
  document.getElementById('drawer-overlay').classList.remove('active');
  document.getElementById('task-drawer').classList.remove('active');
}

async function handleSendComment(e, taskId) {
  e.preventDefault();
  const input = document.getElementById('drawer-new-comment');
  const content = input.value.trim();
  if (!content) return;

  try {
    await apiRequest(`/tasks/${taskId}/comments`, 'POST', { content });
    input.value = '';
    await loadGlobalData();
    await openTaskDrawer(taskId);
  } catch (err) {
    alert(`Failed to add comment: ${err.message}`);
  }
}

function openUserModal() {
  document.getElementById('modal-user-title').textContent = 'Add New User';
  document.getElementById('user-form').reset();
  document.getElementById('user-edit-id').value = '';
  document.getElementById('group-u-password').style.display = 'block';
  document.getElementById('group-u-active').style.display = 'none';
  document.getElementById('modal-user').classList.add('active');
}

function openEditUserModal(id) {
  const u = state.users.find(item => item.id === id);
  if (!u) return;
  document.getElementById('modal-user-title').textContent = 'Edit User Profile & Role';
  document.getElementById('user-edit-id').value = u.id;
  document.getElementById('u-name').value = u.full_name;
  document.getElementById('u-email').value = u.email;
  document.getElementById('u-role').value = u.role;
  document.getElementById('u-active').checked = u.is_active;
  document.getElementById('group-u-active').style.display = 'block';
  document.getElementById('group-u-password').style.display = 'none';
  document.getElementById('modal-user').classList.add('active');
}

async function handleSaveUser(e) {
  e.preventDefault();
  const id = document.getElementById('user-edit-id').value;
  const fullName = document.getElementById('u-name').value;
  const email = document.getElementById('u-email').value;
  const role = document.getElementById('u-role').value;

  try {
    if (id) {
      const isActive = document.getElementById('u-active').checked;
      await apiRequest(`/users/${id}`, 'PUT', { full_name: fullName, email, role, is_active: isActive });
    } else {
      const password = document.getElementById('u-password').value;
      await apiRequest('/users', 'POST', { full_name: fullName, email, password, role });
    }
    closeModal('modal-user');
    await loadGlobalData();
    navigate('team');
  } catch (err) {
    alert(`Error saving user: ${err.message}`);
  }
}

async function toggleUserActive(userId, newActive) {
  try {
    await apiRequest(`/users/${userId}`, 'PUT', { is_active: newActive });
    await loadGlobalData();
    navigate('team');
  } catch (err) {
    alert(`Could not change user status: ${err.message}`);
  }
}

function closeModal(id) { document.getElementById(id).classList.remove('active'); }

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}

function formatDate(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatDateOnly(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
