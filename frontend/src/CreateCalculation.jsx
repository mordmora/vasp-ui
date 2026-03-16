import React, { useState } from 'react';
import './CreateCalculation.css';

const CreateCalculation = ({ onBack }) => {
    const [selectedType, setSelectedType] = useState('Relajacion');

    return (
        <div className="create-calc-container">
            <header className="create-calc-header">
                <button className="back-button" onClick={onBack}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 12H5" stroke="#EAEAEA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M12 19L5 12L12 5" stroke="#EAEAEA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Volver
                </button>
                <h1>Crear nuevo calculo</h1>
                <div className="header-placeholder"></div> {/* To balance the header center title */}
            </header>

            <main className="create-calc-main">
                <div className="calc-details-wrapper">
                    <div className="input-group name-input-group">
                        <label>Nombre:</label>
                        <input type="text" className="calc-name-input" />
                    </div>

                    <div className="calc-columns">
                        <div className="left-column">
                            <div className="type-selector">
                                {['Relajacion', 'SCF', 'Estructura de bandas', 'Densidad de estados'].map((type) => (
                                    <div
                                        key={type}
                                        className={`type-option ${selectedType === type ? 'selected' : ''}`}
                                        onClick={() => setSelectedType(type)}
                                    >
                                        {type}
                                    </div>
                                ))}
                                <div className="scroll-indicator"></div>
                            </div>

                            <div className="working-directory-section">
                                <div className="folder-label">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M10 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20H20C21.1046 20 22 19.1046 22 18V8C22 6.89543 21.1046 6 20 6H12L10 4Z" stroke="#B0B3B8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                    <span>Directorio de trabajo</span>
                                </div>
                                <div className="browse-link">Examinar...</div>
                            </div>
                        </div>

                        <div className="right-column">
                            <div className="info-text">
                                VGUI usa vaspkit para preparar el calculo, si no especificas un INCAR, se usa el que genera vaspkit.
                            </div>
                            <div className="files-container">
                                {['INCAR', 'POSCAR', 'POTCAR', 'KPOINTS'].map((file) => (
                                    <div key={file} className="file-input-item">
                                        <label>{file}:</label>
                                        <div className="file-input-box">
                                            {file === 'POSCAR' ? (
                                                <span className="browse-placeholder">examinar...</span>
                                            ) : (
                                                <>
                                                    <span className="file-icon-small">📄</span>
                                                    <span className="file-path">/home/user/calculo/SmCaFe06/{file}</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            <footer className="create-calc-footer">
                <div className="divider-line"></div>
                <button className="next-button">Siguiente</button>
            </footer>
        </div>
    );
};

export default CreateCalculation;
