import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import GameCreator from "./GameCreator";
import CurrentGame from "./CurrentGame";
import CurrentGamePlayer from "./CurrentGamePlayer"; // Import new component

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<GameCreator />} />
        <Route path="/current-game/:gameCode" element={<CurrentGame />} />
        <Route path="/current-game-player/:playerId" element={<CurrentGamePlayer />} /> {/* New route */}
      </Routes>
    </Router>
  );
};

export default App;
