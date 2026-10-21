# 💧 PurifyX | AI-Powered Smart Water Quality Assessment & Treatment Prototype

**An intelligent water quality monitoring and assessment system integrating Artificial Intelligence, Internet of Things (IoT), embedded electronics, and experimental filtration techniques.**

PurifyX is an AI-assisted water quality assessment prototype designed to explore how real-time sensor data, machine learning, and water treatment techniques can work together to support more informed water quality evaluation.

By integrating an ESP32-based sensing system with a machine learning classification model and a desktop monitoring dashboard, PurifyX aims to make water quality assessment more accessible, structured, and data-driven.

> **Project focus:** Smart sensing · TinyML · IoT · Water quality assessment · Experimental filtration · Data visualization

---

## 📌 Table of Contents

- [Overview](#-overview)
- [The Problem](#-the-problem)
- [Our Approach](#-our-approach)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Hardware Components](#-hardware-components)
- [Software and Technologies](#-software-and-technologies)
- [AI and Machine Learning](#-ai-and-machine-learning)
- [Experimental Filtration](#-experimental-filtration)
- [Desktop Monitoring Dashboard](#-desktop-monitoring-dashboard)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Testing and Evaluation](#-testing-and-evaluation)
- [Limitations and Safety](#-limitations-and-safety)
- [Future Development](#-future-development)
- [Contributions](#-contributions)
- [Acknowledgements](#-acknowledgements)
- [License](#-license)

---

## 🌍 Overview

Access to reliable water quality assessment remains an important challenge in communities, field environments, and resource-constrained settings.

Conventional water testing can require specialized equipment, laboratory access, and trained personnel. PurifyX explores a compact, technology-driven approach that combines electronic sensing, machine learning, and experimental filtration in an integrated prototype.

The system is designed around four principal components:

1. **Smart sensing:** Collects water quality measurements through connected sensors.
2. **AI-assisted assessment:** Processes sensor-derived information through a machine learning model to generate a classification.
3. **Experimental filtration:** Investigates changes in selected water characteristics following treatment.
4. **Digital monitoring:** Presents readings and assessment results through a Python-based dashboard, with logging and report generation.

The long-term vision is to explore affordable, scalable, and data-driven water assessment systems suitable for further research and field validation.

## 🎯 The Problem

Water quality is influenced by multiple physical and chemical parameters. Evaluating only one measurement can provide an incomplete picture of water quality.

A practical assessment system should therefore aim to:

- Monitor multiple measurable parameters.
- Interpret sensor readings systematically.
- Present results in an accessible format.
- Record measurements for subsequent analysis.
- Support investigation of treatment methods.
- Communicate uncertainty and limitations clearly.

PurifyX approaches this challenge by combining embedded sensing, AI-assisted interpretation, and digital reporting in a unified prototype.

## 💡 Our Approach

PurifyX integrates hardware and software into a single experimental workflow.

**Step 1 — Data acquisition**

The ESP32 interfaces with water quality sensors to collect measurements such as pH, turbidity, total dissolved solids (TDS), and temperature.

**Step 2 — Data processing**

The acquired measurements are organized and prepared for interpretation by the assessment pipeline.

**Step 3 — AI-assisted classification**

A trained machine learning model evaluates the available input features and produces a classification from the categories defined during model development.

**Step 4 — Monitoring and reporting**

The desktop dashboard presents available readings and assessment results, while supporting data logging and PDF report generation.

**Step 5 — Experimental treatment evaluation**

Selected samples can be assessed before and after experimental filtration to investigate changes in measured parameters.

The sensing, classification, and filtration components have distinct roles. An AI classification is an assessment output, while filtration performance must be established through appropriate experimental measurements.

## ✨ Key Features

- **Multi-parameter water sensing:** Integration of pH, turbidity, TDS, and temperature measurements.
- **ESP32-based embedded system:** Microcontroller-driven sensor acquisition and hardware interfacing.
- **TinyML-based classification:** Machine learning inference for categorizing sensor-derived inputs.
- **AI assessment categories:** Safe, Treat, Unsafe, and Uncertain, as defined by the current model.
- **Experimental filtration:** Investigation of changes in selected sample characteristics after treatment.
- **Interactive desktop dashboard:** Python and PyQt6-based interface for monitoring and assessment.
- **Data logging:** Recording of available measurements and system results.
- **PDF report generation:** Structured reporting of recorded assessment information.
- **Modular architecture:** Scope for adding sensors, improving the model, and expanding analytical capabilities.

## 🏗️ System Architecture

The prototype follows a modular sensing-to-reporting workflow.

```
                  WATER SAMPLE
                       |
                       v
             +--------------------+
             | Water Quality      |
             | Sensors            |
             | pH / Turbidity     |
             | TDS / Temperature  |
             +--------------------+
                       |
                       v
             +--------------------+
             | ESP32 Embedded     |
             | Data Acquisition   |
             +--------------------+
                       |
                       v
             +--------------------+
             | Data Processing &  |
             | Model Input        |
             +--------------------+
                       |
                       v
             +--------------------+
             | TinyML / AI Model  |
             | Classification     |
             +--------------------+
                       |
                       v
             +--------------------+
             | Python / PyQt6     |
             | Monitoring GUI     |
             +--------------------+
                  |           |
                  v           v
             Data Logs     PDF Reports

       Experimental Filtration
       evaluated separately using
       appropriate before-and-after
       measurements and controls.
```

*Note: The diagram represents the intended high-level workflow. Exact communication interfaces and the deployment location of model inference should be documented according to the final implementation.*

## 🔧 Hardware Components

| Component                         | Purpose                                                     |
| --------------------------------- | ----------------------------------------------------------- |
| ESP32 microcontroller             | Embedded processing and sensor interfacing                  |
| pH sensor                         | Measurement of sample acidity or alkalinity                 |
| Turbidity sensor                  | Estimation of suspended-particle-related optical scattering |
| TDS sensor                        | Estimation of total dissolved solids from sensor response   |
| Temperature sensor                | Measurement of sample temperature                           |
| Display and indicators            | Local system feedback, where implemented                    |
| Experimental filtration materials | Investigation of selected treatment approaches              |

Additional components may be incorporated as the prototype evolves.

Sensor accuracy depends on calibration, sensor quality, environmental conditions, and the characteristics of the sample being measured.

## 💻 Software and Technologies

| Technology               | Application                                                                                           |
| ------------------------ | ----------------------------------------------------------------------------------------------------- |
| Python                   | Application logic, data processing, and reporting                                                     |
| PyQt6                    | Desktop graphical user interface                                                                      |
| ESP32 / Embedded C++     | Firmware and hardware interfacing                                                                     |
| Edge Impulse             | Machine learning model development and evaluation                                                     |
| TinyML                   | Lightweight machine learning inference workflows                                                      |
| Serial communication     | Potential or implemented data exchange between hardware and computer, depending on the final firmware |
| PDF generation libraries | Automated report creation, depending on the implementation                                            |

## 🧠 AI and Machine Learning

PurifyX incorporates a machine learning model developed using Edge Impulse for classification of sensor-derived inputs.

### Classification categories

The current model uses four assessment categories:

| Class     | Intended interpretation                                              |
| --------- | -------------------------------------------------------------------- |
| Safe      | Sample classified into the model's designated safe category          |
| Treat     | Sample assigned to the treatment category                            |
| Unsafe    | Sample classified into the model's designated unsafe category        |
| Uncertain | Sample assigned to an uncertain category, where defined by the model |

These labels describe the model's learned classification scheme. They must not be interpreted as certified determinations of drinking-water safety.

### Reported development metrics

The following are development figures reported for the current model and should be associated with the exact model version and evaluation dataset when published.

| Metric                       | Reported value |
| ---------------------------- | -------------: |
| Training samples / records   |        226,171 |
| Validation samples / records |         56,543 |
| Reported accuracy            |         99.93% |

The sample counts above refer to the reported model-development dataset and do not necessarily represent independent physical water samples.

Accuracy alone does not establish the model's reliability in real-world deployment. Further documentation should include the dataset composition, class distribution, collection methodology, train-validation separation, confusion matrix, per-class precision and recall, and independent testing on samples not used during model development.

### Model development goals

- Improve robustness across different water samples and environmental conditions.
- Evaluate model performance on independently collected data.
- Examine misclassification and uncertainty.
- Investigate lightweight deployment on embedded hardware where feasible.
- Establish reproducible evaluation procedures.

## 🧪 Experimental Filtration

PurifyX also investigates filtration techniques as part of its broader water treatment research.

The prototype has undergone experimental testing using a prepared sample, with visual changes observed during filtration, including a substantial reduction in visible yellow coloration.

These observations provide a basis for further investigation but do not, on their own, establish contaminant removal efficiency or drinking-water safety.

### Future experimental evaluation

A more rigorous treatment study should include:

- Documented sample preparation and initial conditions.
- Measurements before and after each treatment stage.
- Repeated trials and appropriate control samples.
- Calibrated sensor readings and measurement uncertainty.
- Quantitative comparison of turbidity, pH, TDS, and other relevant parameters.
- Laboratory testing for contaminants that the prototype cannot detect.

The filtration process and the sensing system should be evaluated independently before conclusions are drawn about treatment effectiveness.

## 📊 Desktop Monitoring Dashboard

The PurifyX desktop application is developed using Python and PyQt6.

The dashboard is intended to provide a convenient interface for viewing system measurements and assessment results.

### Dashboard capabilities

- Display of available sensor readings.
- Presentation of AI classification results.
- Data logging for subsequent review.
- PDF report generation.
- Support for structured monitoring and experimental documentation.

Screenshots and a demonstration video can be added here as the interface is prepared for publication.

\<!-- Add project screenshots to the repository and replace the placeholder below. -->

\<!-- ![PurifyX Dashboard]\(docs/images/dashboard.png) -->

## 📁 Project Structure

The repository can be organized using the following structure. Adjust the filenames to match the actual implementation.

```
purifyx-ai-water-monitoring/
│
├── firmware/
│   ├── src/
│   └── README.md
│
├── dashboard/
│   ├── src/
│   └── requirements.txt
│
├── model/
│   └── README.md
│
├── docs/
│   ├── images/
│   ├── architecture/
│   └── testing/
│
├── reports/
│   └── README.md
│
├── .gitignore
├── README.md
└── LICENSE
```

This is a suggested layout, not a claim that every listed directory or file currently exists.

Large model artifacts, generated reports, raw datasets, and hardware design files should be added selectively according to repository size, permissions, and reproducibility requirements.

## 🚀 Getting Started

Installation instructions will depend on the final project structure and the communication interface used by the firmware.

### Prerequisites

- Python 3.x, compatible with the selected application dependencies.
- Git, for cloning and version control.
- The required ESP32 development environment.
- Compatible water quality sensors and associated circuitry.
- A USB data cable for hardware programming and communication, where applicable.

### Clone the repository

```bash
git clone https://github.com/harshsharma1447/purifyx-ai-water-monitoring.git

cd purifyx-ai-water-monitoring
```

Replace `YOUR-USERNAME` with the actual GitHub account username.

### Set up the Python environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or, using Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Install the project dependencies once the repository's `dashboard/requirements.txt` has been populated:

```bash
pip install -r dashboard/requirements.txt
```

The actual application launch command, model setup, firmware upload procedure, and hardware configuration should be documented after the relevant source files have been published.

## 🧪 Testing and Evaluation

PurifyX is an evolving prototype. Evaluation should cover the sensing hardware, machine learning model, software application, and filtration experiments separately.

Suggested evaluation areas include:

- Sensor calibration and repeatability.
- Agreement with suitable reference measurements.
- Model performance on independent test data.
- Correct handling of missing or invalid readings.
- Reliability of data logging and PDF report generation.
- Reproducibility of before-and-after filtration experiments.
- Robustness across different sample conditions.

Results should be accompanied by the corresponding testing conditions, measurement units, and methodology.

## ⚠️ Limitations and Safety

PurifyX is a research and development prototype, not a certified water testing laboratory or a validated drinking-water purification device.

- Sensor readings do not detect every physical, chemical, or microbiological hazard.
- TDS, pH, and turbidity measurements alone cannot establish that water is safe to drink.
- Machine learning predictions depend on the quality, coverage, and representativeness of the training data.
- Visual clarity after filtration does not establish the absence of harmful contaminants.
- Nanoparticle-based treatment methods require careful evaluation of material composition, possible leaching, residual particles, and disposal.
- Claims of purification or potability require suitable independent testing against applicable drinking-water standards.

**Do not use water processed by this prototype for drinking or food preparation unless its safety has been independently established through appropriate testing and validated treatment procedures.**

## 🔭 Future Development

Potential areas of further development include:

- Improved sensor calibration and reliability.
- More extensive and diverse training datasets.
- Independent validation of the classification model.
- Quantitative evaluation of experimental filtration performance.
- Additional sensors and monitoring parameters.
- Enhanced dashboard visualizations and historical trend analysis.
- More detailed reporting and reproducibility features.
- Embedded inference and edge deployment, where technically appropriate.
- Field testing under controlled and documented conditions.

## 🤝 Contributions

Contributions, technical discussions, and constructive feedback are welcome, subject to the project's ownership, collaboration agreements, and publication constraints.

Before contributing, please document proposed changes clearly and ensure that any shared code, datasets, designs, or research material may legally be redistributed.

For substantial contributions, open an issue or discuss the proposed change with the maintainers before submitting a pull request.

## 🙏 Acknowledgements

PurifyX builds on the broader work of the embedded systems, IoT, machine learning, and water quality research communities.

Acknowledgements for individual contributors, collaborators, mentors, and supporting institutions should be added with their permission and in accordance with the project's contribution and publication agreements.

## 📜 License

No open-source license has been specified yet.

A license should be selected after the project maintainers have confirmed ownership and permissions for the software, documentation, hardware designs, and any third-party components.

---

**PurifyX | Exploring smarter, data-driven approaches to water quality assessment.**

*Built through experimentation, engineering, and the integration of AI, IoT, and embedded systems.*
