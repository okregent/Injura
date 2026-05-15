# Injura — System Overview

## Tech Stack
- **Frontend**: React Native + Expo
- **Backend**: FastAPI + Python
- **Computer Vision**: MediaPipe Pose + OpenCV
- **Database & Storage**: PostgreSQL / Supabase
- **Deployment**: Render or AWS

## Architecture Flow
```
Mobile App → API Layer → Analysis Engine → Storage / Database
```

This structure improves deployment flexibility and long-term maintainability.

## AI Engineering Focus
The project focuses on practical AI engineering rather than custom model training. The system integrates pretrained pose estimation models with custom movement analysis and personalised inference logic.
