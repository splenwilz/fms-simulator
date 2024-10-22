# FMS (Farm Management System) Simulator

This is a Farm Management System (FMS) simulator developed with Flask and MySQL, allowing you to manage paddocks, mobs, and animals. The system simulates pasture growth and animal consumption, with the ability to move to the next day and track daily changes.

## Features

- **Manage Paddocks**: Create paddocks with areas and pasture details, with dropdown selections for predefined paddocks.
- **Manage Mobs**: Assign mobs to paddocks and track the number of animals in each mob.
- **Manage Animals**: Add animals to mobs, track their weight and age based on the date of birth.
- **Daily Simulation**: Simulate pasture growth and animal consumption by moving to the next day.
- **Pasture & Stock Calculations**: Automatically calculates Total Dry Matter (DM) based on pasture growth and animal consumption rates.
- **Database Reset**: Reset the database back to initial values.
  
## Table of Contents

- [Installation](#installation)
- [Database Structure](#database-structure)
- [Usage](#usage)
- [Simulation Details](#simulation-details)
- [Routes](#routes)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.x
- MySQL server
- Virtualenv (Optional but recommended)

### Steps

1. **Clone the repository**

    ```bash
    git clone https://github.com/splenwilz/fms-simulator.git
    cd fms-simulator
    ```

2. **Set up a virtual environment (optional but recommended)**

    ```bash
    python3 -m venv venv
    source venv/bin/activate    # For Linux/Mac
    # OR
    venv\Scripts\activate       # For Windows
    ```

3. **Install required dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the database**

    - Create a MySQL database for the project.
    - Update the database connection details in `app.py`:

      ```python
      db_connection = mysql.connector.connect(
          host="localhost",
          user="root",
          password="your_password",
          database="fms"
      )
      ```

5. **Run the migration script**

    Execute the provided SQL migration script to set up the database structure:

    ```bash
    mysql -u root -p fms < fms-local.sql
    ```

6. **Start the application**

    ```bash
    flask --app app run --port 5001
    ```

7. **Access the application**

    Open a browser and navigate to [http://127.0.0.1:5001](http://127.0.0.1:5001).

## Database Structure

The Farm Management System uses a MySQL database with the following tables:

- **curr_date**: Tracks the simulation's current date.
- **paddocks**: Contains paddock details including area and Dry Matter (DM) rates.
- **mobs**: Groups of animals assigned to paddocks.
- **animals**: Individual animals with weight, date of birth, and mob assignment.
- **stock**: Stock data recording mob-related stock information.

### Example Schema

```sql
CREATE TABLE curr_date (
    curr_date DATE NOT NULL,
    PRIMARY KEY (curr_date)
);

CREATE TABLE paddocks (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    area FLOAT(2) DEFAULT NULL,
    dm_per_ha FLOAT(2) DEFAULT NULL,
    total_dm FLOAT(2) DEFAULT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE mobs (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50),
    paddock_id INT,
    PRIMARY KEY (id),
    CONSTRAINT fk_paddock FOREIGN KEY (paddock_id) REFERENCES paddocks(id)
);

CREATE TABLE animals (
    id INT NOT NULL AUTO_INCREMENT,
    animal_name VARCHAR(50),
    mob_id INT,
    paddock_id INT,
    dob DATE NOT NULL,
    weight FLOAT(2) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_mob FOREIGN KEY (mob_id) REFERENCES mobs(id),
    CONSTRAINT fk_paddock_animals FOREIGN KEY (paddock_id) REFERENCES paddocks(id)
);
```

## Usage

### Moving to the Next Day

You can simulate moving to the next day by calculating pasture growth and animal consumption for each paddock. Use the "Next Day" button on the paddocks page to apply these calculations and update the total Dry Matter (DM) values.

### Reset the Database

The `/reset` route allows you to reset the database to its initial state. This route will:

- Set the current date back to the starting date.
- Remove all animals, mobs, and paddocks, and repopulate them with default values.

## Simulation Details

- **Pasture Growth Rate**: 65 kg DM/ha/day
- **Stock Consumption Rate**: 14 kg DM/animal/day
- **Total DM Calculation**:

    ```
    Total DM = Starting Total DM + Pasture Growth Rate - (Stock Consumption Rate * Number of Stocks)
    ```

- **Animal Age Calculation**: Animal age is automatically calculated based on the animal's date of birth (`dob`) and the current date in the simulation.

## Routes

### Core Routes

| Route            | Method | Description                                   |
|------------------|--------|-----------------------------------------------|
| `/`              | GET    | Home page                                     |
| `/paddocks`      | GET    | View paddock details                          |
| `/create_paddock`| GET/POST | Create a new paddock                        |
| `/create_mob`    | GET/POST | Create a new mob                            |
| `/create_animal` | GET/POST | Create a new animal                         |
| `/next_day`      | POST   | Move the simulation to the next day           |
| `/reset`         | GET    | Reset the database to its initial state       |

### Example Route Definitions

- **Create Paddock**: Allows the user to create a paddock by selecting from a dropdown of predefined paddocks that don't have associated values for area and DM.

    ```python
    @app.route("/create_paddock", methods=["GET", "POST"])
    def create_paddock():
        ...
    ```

- **Reset Database**: Resets the entire database to its initial state.

    ```python
    @app.route("/reset")
    def reset():
        ...
    ```

## Contributing

Contributions are welcome! Please fork the repository, make your changes, and submit a pull request.

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Create a new pull request