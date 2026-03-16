import React from 'react';
import './Dashboard.css';

const Dashboard = ({ onNavigateCreate }) => {
    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div className="logo-section">
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M20 0L40 34.641H0L20 0Z" fill="#EAEAEA" /> {/* Placeholder V logo */}
                        <path d="M14 12L20 22L26 12H30L20 29L10 12H14Z" fill="#1E2126" /> {/* Cutout effect */}
                    </svg>
                    {/* Assuming the logo is an SVG or image, using a placeholder for now conforming to the 'V' shape in screenshot */}
                    <div className="logo-text"></div>
                </div>
                <nav className="dashboard-nav">
                    <a href="#ajustes">Ajustes</a>
                    <a href="#ayuda">Ayuda</a>
                    <a href="#acerca">Acerca de</a>
                </nav>
            </header>

            <main className="dashboard-main">
                <div className="action-buttons">
                    <button className="primary-action" onClick={onNavigateCreate}>
                        <span className="plus-icon">+</span> Crear nuevo calculo
                    </button>
                    <button className="secondary-action">
                        Abrir proyecto
                    </button>
                    <button className="secondary-action">
                        Analizar resultado
                    </button>
                </div>
            </main>

            <footer className="dashboard-footer">
                <div className="footer-content">
                    <div className="recent-projects-section">
                        <div className="section-title">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M10 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20H20C21.1046 20 22 19.1046 22 18V8C22 6.89543 21.1046 6 20 6H12L10 4Z" stroke="#EAEAEA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            <span>Proyectos recientes</span>
                        </div>
                        <div className="project-list">
                            <div className="project-item">
                                <span className="file-icon">📄</span>
                                <span>SmCaFe06</span>
                            </div>
                            <div className="project-item">
                                <span className="file-icon">📄</span>
                                <span>Grafeno_S</span>
                            </div>
                        </div>
                    </div>

                    <div className="status-bar">
                        <div className="status-item">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M3 3H21C22.1046 3 23 3.89543 23 5V15C23 16.1046 22.1046 17 21 17H3C1.89543 17 1 16.1046 1 15V5C1 3.89543 1.89543 3 3 3Z" stroke="#EAEAEA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M7 21H17" stroke="#EAEAEA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M12 17V21" stroke="#EAEAEA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            <span>Conectado a cluster_loc1 | 2 Calculos activos</span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Dashboard;
