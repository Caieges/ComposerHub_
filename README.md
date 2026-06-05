ComposerHub
#### Video Demo: https://youtu.be/0ia7SS1bKeM
#### Description:

ComposerHub is a full-stack web application designed for film, television, and media composers to manage scoring projects and cue workflow.

The application was built as my final project for CS50x. My background is in composition for media, which includes working with DAWs, collaborating with musicians, and working with scores for orchestras. I created a practical tool that connects to real-world composer workflows.

ComposerHub allows users to:
- Create and manage scoring projects
- Organize cues within each project
- Track cue progress throughout the scoring process
- Upload and preview reference audio and files
- Store production notes

The goal of the project is to give composers a centralized place for handling the logistical side of media composition.

The main features include:

**User Authentication System**

ComposerHub includes a user authentication system that lets users:
- Register an account
- Log in
- Log out
- Maintain isolated personal projects

Passwords are hashed using Werkzeug's `generate_password_hash` function before being stored in a SQLite database.

**Project Management**

Once logged in, users can create projects that contain:
- Project title
- Project description
- Creation timestamp
- Cue list
- Project reference files

Projects can also be edited or deleted.

**Cue Workflow System**

Inside every project, users can create individual cues, each of which contains:
- Cue title
- Start timecode
- Duration
- Notes
- Workflow status, including:
    - Sketching
    - Orchestration
    - Recording
    - Mixing
    - Done
- Attached files

Users can upload files, and edit or delete cues.

A visual progress bar shows completed cues / total cues.

**File Upload**

Supported upload file types include:
- PDF, TXT, DOC, DOCX
- MP3, WAV, AIFF, FLAC, M4A
- MP4, MOV, AVI, MKV

All uploads are stored in a local folder.

Media files can be previewed within ComposerHub.

**Technologies Used**

Backend
- Python
- Flask
- SQLite
- Flask-Session
- Werkzeug

Frontend
- HTML
- CSS
- JavaScript
- Jinja templates

**Database Structures**

users
    - User ID
    - Username
    - Password hash

projects
    - Project metadata
    - Project owner (user)

cues
    - Cue information
    - Workflow status
    - Timecodes
    - Notes
    - Related project

files
    - Uploaded file metadata
    - Cue / project relationships
    - Stored filename
    - Original filename
    - File type


**Design Decisions**

Professional media composers typically work cue-by-cue rather than treating an entire film score as a single item. Cues are sorted by start timecode so users can quickly find a specific cue. The traditional cue management workflow often relies on a maze of folders that become congested as the number of cues increases. ComposerHub reduces this inconvenience and stores everything in a user-friendly environment.

The dark theme was chosen to reflect the color palette of traditional DAWs and to accommodate low-light studio environments, making it more comfortable for the eyes during extended use.

**Future Improvements**

Potential future features include:
- Calendar deadlines
- DAW session tracking
- Collaboration tools
- Cloud storage integration
- Search and filtering
- Music notation preview support
- Mobile optimization

**Running the Application**

Install dependencies:

`pip install flask-session werkzeug`

Run the Flask application:

`flask --app app run --debug`

Open in browser:

https://127.0.0.1:5000

**Final Notes**

ComposerHub was designed as a practical, production-oriented tool rather than a purely academic demonstration.

By combining my background in music composition with the programming concepts learned throughout CS50, I aimed to create an application that reflects genuine industry workflow needs while demonstrating full-stack web development skills.

