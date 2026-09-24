import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Import the json form of ChatBox from ChatBox.js
import ChatBox from './ChatBox';

function App() {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState('');

  const API_URL = 'http://localhost:8000/api/tasks/';

  // Fetch tasks on load
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await axios.get(API_URL);
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const addTask = async () => {
    if (!newTask.trim()) return;
    try {
      const response = await axios.post(API_URL, {
        title: newTask,
        completed: false,
      });
      setTasks([...tasks, response.data]);
      setNewTask('');
    } catch (error) {
      console.error('Error adding task:', error);
    }
  };

  const toggleTask = async (task) => {
    try {
      const response = await axios.patch(`${API_URL}${task.id}/`, {
        completed: !task.completed,
      });
      setTasks(tasks.map(t => (t.id === task.id ? response.data : t)));
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  return (
    <div className="App">
      <h1>Django + React Tasks</h1>

      <ChatBox />

      <div>
        <input
          type="text"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          placeholder="New task..."
        />
        <button onClick={addTask}>Add</button>
      </div>

      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <label>
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => toggleTask(task)}
              />
              {task.title}
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;