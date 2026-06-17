# EARS to Gherkin Converter - Application Features Report

This document outlines the comprehensive feature set of the **EARS to Gherkin Converter**, a desktop application designed to streamline the software requirements engineering workflow.

## 1. Core Workflow Features
---

### EARS Requirement Input
- **Direct Entry:** Users can type or paste requirements directly into the EARS Requirement Input text area.
- **State Management:** The application maintains a persistent list of requirements on the left-hand pane, allowing the user to seamlessly click through multiple requirements without losing their work.
- **Clear All:** A simple button to wipe the slate clean and start fresh.

### Gherkin Generation
- **LLM Integration:** Connects to NVIDIA's Nemotron model (or any OpenAI-compatible API) to perform semantic translation of EARS syntax into standardized Gherkin (Feature, Scenario, Given, When, Then).
- **Intelligent Prompting:** The application classifies the requirement (e.g., Event-driven, State-driven, Optional) before sending it to the LLM, giving the AI specific hints on how to structure the Gherkin output.
- **Live Preview:** A toggleable mode that automatically converts the requirement in the background after 800ms of inactivity (typing debounce).
- **Export & Clipboard:** Quickly copy the generated Gherkin to the clipboard or export it directly to a `.feature` file.

### CSV Batch Import
- **Intelligent Column Detection:** When importing a `.csv` file, the app automatically sniffs headers for keywords like "requirement", "content", "req", or "ears" to find the correct column.
- **Bulk Loading:** Loads all requirements from the CSV into the left-hand navigation list, allowing the user to step through and process them individually.

## 2. Review and Validation Workflow
---

### AI Requirement Review
- **Validation Engine:** A dedicated "Review Requirement" feature that tasks the LLM with strictly evaluating the input text to ensure it adheres to the EARS template structure and is practically testable.
- **Visual Tracking:** 
  - Requirements that pass review are marked with a **`[✓]`** prefix in the list.
  - Requirements that fail review or contain structural issues are flagged with a **`[!]`** prefix.
- **Basic Structural Validation:** The Gherkin output is also scanned locally for required keywords (`Feature:`, `Scenario:`, `Given`, `When`, `Then`). Invalid output turns the text box red.

### Collaboration & Email Integration
- **Batch Flagging:** Failed requirements are held in a "Flagged" state.
- **Mail Req. Engineer:** A single click automatically compiles all flagged requirements and the specific issues identified by the AI into an email draft, launching the user's default email client (e.g., Outlook, Apple Mail) so they can instantly request revisions from the Requirements Engineer.

## 3. Advanced Context & Reliability
---

### Qdrant Vector DB Integration (RAG)
- **Local Embedded Database:** The application uses `fastembed` out-of-the-box to generate document embeddings in memory, requiring no external embedding APIs.
- **Context Management:** A dedicated "RAG Context" tab allows users to create collections and upload architectural documents, feature dictionaries, or domain-specific rules.
- **Semantic Injection:** During Gherkin conversion, the app queries the active Qdrant collection for documents semantically similar to the current requirement, and injects them into the LLM prompt to heavily improve the accuracy and context-awareness of the generated test cases.

### Resiliency & Auditing
- **Exponential Backoff:** If the LLM returns an empty response, a `NoneType`, or if the network fails, the API client automatically retries the call using an exponential backoff strategy.
- **Session Settings:** Users can adjust the "Max Retries" limit on the fly in the Settings tab without permanently modifying environment variables.
- **Raw AI Log Viewer:** A dedicated audit button allows the user to view the pure, unmodified JSON or text string returned by the AI before the application parsed it, ensuring transparency in how the AI evaluated or converted the text.

## 4. UI/UX Design
---

### iOS-Inspired Aesthetics
- The application is built with `tkinter` but aggressively styled to mimic modern, clean iOS aesthetics.
- Utilizes a sleek palette of light grays (`#F2F2F7`), crisp white panels (`#FFFFFF`), and vibrant blue accents (`#007AFF`).
- **Master-Detail Layout:** A split-pane design with a navigational list on the left and a detailed workspace on the right, keeping the interface uncluttered while handling large batches of requirements.
- **Tabbed Navigation:** Distinct tabs separate the Core Editor, RAG Context Management, and Session Settings, preventing UI overload.
