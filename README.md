# Habit Tracker

A simple, user-friendly web app to help you build and track your daily habits.  
Built with Flask, SQLite, and Bootstrap-inspired styling.

---

## Features

- Add, edit, and delete habits
- Mark habits as Done, Skipped, or Undo status for today
- View habit streaks: total completions, current streak, and longest streak
- View history of habit completions by month
- Responsive and clean UI

---

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/batrisyiasafri/habit_tracker.git
   cd habit-tracker


1. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

3. Initialize the database:

flask db upgrade  # or if you don't use migrations, just run the app and it will create the DB

4. Run the app:
   ```bash
   flask run

5. Open your browser and visit http://localhost:5000

## Usage
- Add new habits via the input box on the homepage.

- Use the action links next to each habit to mark it done, skipped, or undo today's status.

- Edit or delete habits as needed.

- Navigate to habit history for a detailed monthly calendar view.

## Configuration
- Default user ID is set to 1 for demo purposes.

- To implement authentication, modify the user session logic accordingly.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contributions
Feel free to open issues or submit pull requests. Any contributions are welcome!

## Contact
Created by Batrisyia Safri
Project Link: https://github.com/batrisyiasafri/habit_tracker