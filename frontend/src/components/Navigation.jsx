import { NavLink, useLocation, Link } from 'react-router-dom';

export default function Navigation({ docName, docId, theme, onToggleTheme }) {
  const location = useLocation();
  const isDocView = location.pathname !== '/' && docId;

  return (
    <nav className="nav" id="main-nav">
      <Link to="/" className="nav__brand" id="nav-brand">
        RAGGED
      </Link>

      {isDocView && docName && (
        <span className="nav__doc-name" id="nav-doc-name">{docName}</span>
      )}

      <div className="nav__links">
        {isDocView && (
          <>
            <NavLink
              to={`/cheatsheet/${docId}`}
              className={({ isActive }) => `nav__link ${isActive ? 'nav__link--active' : ''}`}
              id="nav-link-cheatsheet"
            >
              Cheat Sheet
            </NavLink>
            <span className="nav__separator">/</span>
            <NavLink
              to={`/reference/${docId}`}
              className={({ isActive }) => `nav__link ${isActive ? 'nav__link--active' : ''}`}
              id="nav-link-reference"
            >
              Reference
            </NavLink>
            <span className="nav__separator">/</span>
            <NavLink
              to={`/report/${docId}`}
              className={({ isActive }) => `nav__link ${isActive ? 'nav__link--active' : ''}`}
              id="nav-link-report"
            >
              Report
            </NavLink>
          </>
        )}
        <button
          className="nav__theme-toggle"
          onClick={onToggleTheme}
          id="theme-toggle"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? '☀' : '☾'}
        </button>
      </div>
    </nav>
  );
}
