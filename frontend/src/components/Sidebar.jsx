import { useState, useEffect } from 'react'

// Navigation configuration
const navItems = [
  { path: '/dashboard', icon: '📊', label: '数据看板' },
  { path: '/search', icon: '🔍', label: '数据检索' },
  { path: '/qa-records', icon: '💬', label: '原始问答' },
  { path: '/insights', icon: '💡', label: '经验沉淀' },
  { path: '/settings', icon: '⚙️', label: '系统管理', roles: ['superadmin'] }, // Restricted
]

export function Sidebar({ collapsed, onToggle }) {
  const [location, setLocation] = useState(window.location.hash || '#/dashboard')
  const [userRole, setUserRole] = useState(localStorage.getItem('clm_role') || 'admin')

  // Listen for hash changes to update active state
  useEffect(() => {
    const h = () => {
      setLocation(window.location.hash || '#/dashboard')
      setUserRole(localStorage.getItem('clm_role') || 'admin')
    }
    window.addEventListener('hashchange', h)
    return () => window.removeEventListener('hashchange', h)
  }, [])

  const handleClick = (path) => {
    window.location.hash = path
    setLocation(path)
  }

  const handleLogout = () => {
    localStorage.removeItem('clm_auth_token')
    localStorage.removeItem('clm_role')
    localStorage.removeItem('clm_username')
    window.location.hash = '/login'
  }

  const username = localStorage.getItem('clm_username') || '管理员'

  // Filter items based on role
  const visibleItems = navItems.filter(item => {
    if (item.roles) {
      return item.roles.includes(userRole)
    }
    return true
  })

  return (
    <aside className={`bg-slate-900 text-white flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-56'}`}>
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-slate-700">
        {!collapsed && <span className="text-lg font-bold">CLM 管理后台</span>}
        {collapsed && <span className="text-lg font-bold mx-auto">CLM</span>}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {visibleItems.map(item => {
          const hashPath = item.path
          const isActive = location === hashPath || (location === '#/' && hashPath === '#/dashboard')
          return (
            <button
              key={item.path}
              onClick={() => handleClick(item.path)}
              className={`w-full flex items-center px-4 py-3 text-sm hover:bg-slate-800 transition-colors ${isActive ? 'bg-slate-800 text-blue-400 border-l-4 border-blue-400' : 'text-slate-300'}`}
            >
              <span className="text-lg">{item.icon}</span>
              {!collapsed && <span className="ml-3">{item.label}</span>}
            </button>
          )
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-slate-700 p-4">
        <div className="flex items-center justify-between">
          {!collapsed && <span className="text-xs text-slate-400 truncate">{username}</span>}
          <button onClick={handleLogout} className="text-slate-400 hover:text-white text-sm" title="退出登录">
            {collapsed ? '🚪' : '退出'}
          </button>
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="h-8 border-t border-slate-700 text-slate-400 hover:text-white text-xs flex items-center justify-center"
      >
        {collapsed ? '▶' : '◀ 收起'}
      </button>
    </aside>
  )
}
