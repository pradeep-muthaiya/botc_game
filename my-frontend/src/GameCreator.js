import React, { useState, useEffect} from "react";
import { useNavigate } from "react-router-dom";
import "./GameCreator.css"; // Import the CSS file

const GameCreator = () => {
  const [gameOption, setGameOption] = useState("Trouble Brewing");
  const [aiGameMaster, setAiGameMaster] = useState(false);
  const [numPlayers, setNumPlayers] = useState(3);
  const [gameCode, setGameCode] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [ipAddress, setIpAddress] = useState(window.location.hostname);

  const navigate = useNavigate();

  const apiUrl = `${ipAddress}:8000`;

  useEffect(() => {
    const storedIp = localStorage.getItem("ip");
    if (storedIp) {
      setIpAddress(storedIp);
    }
  }, []);

  // Function to create a new game
  const handleCreateGame = async () => {
    const gameData = {
      player_count: numPlayers,
      game_version: gameOption,
      ai_game_master: aiGameMaster,
      turn: 0,
      time_of_day: "night",
    };

    try {
      const response = await fetch(`http://${apiUrl}/games/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(gameData),
      });

      const data = await response.json();

      if (data.result === "success") {
        setGameCode(data.game_code);
        console.log("Game created:", data);

        // Navigate to CurrentGame.js with the gameCode
        navigate(`/current-game/${data.game_code}`);
      } else {
        console.error("Game creation failed:", data.errors);
      }
    } catch (error) {
      console.error("Error creating game:", error);
    }
  };

  // Function to join an existing game
  const handleEnterGame = async () => {
    if (!gameCode || !playerName) {
      alert("Please enter a valid game code and name!");
      return;
    }

    const playerData = {
      game_code: gameCode,
      player_name: playerName,
    };

    try {
      const response = await fetch(`http://${apiUrl}/players/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(playerData),
      });

      const data = await response.json();

      if (data.result === "success") {
        console.log("Player created:", data);

        // Navigate to CurrentGamePlayer.js with player_id
        navigate(`/current-game-player/${data.player.player_id}`);
      } else {
        console.error("Player creation failed:", data.error);
      }
    } catch (error) {
      console.error("Error joining game:", error);
    }
  };

  return (
    <div className="game-container">
      <div className="game-creator-container">
      {/* Create Game Section */}
      <h1 className="game-creator-title">Create a Game</h1>

      <select
        className="dropdown"
        value={gameOption}
        onChange={(e) => setGameOption(e.target.value)}
      >
        <option value="Trouble Brewing">Trouble Brewing (Beginner)</option>
        <option value="Bad Moon Rising">Bad Moon Rising (Intermediate)</option>
        <option value="Sects & Violets">Sects & Violets (Intermediate)</option>
      </select>

      <div className="toggle-container">
        <span>AI GameMaster</span>
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={aiGameMaster}
            onChange={() => setAiGameMaster(!aiGameMaster)}
            className="sr-only"
          />
          <span className={`toggle-switch ${aiGameMaster ? "bg-blue-500" : "bg-gray-300"}`}>
            <span className={`toggle-knob ${aiGameMaster ? "toggle-knob-checked" : ""}`} />
          </span>
        </label>
      </div>

      <input
        type="number"
        className="number-input"
        min="3"
        max="20"
        value={numPlayers}
        onChange={(e) => setNumPlayers(Number(e.target.value))}
      />

      <button className="create-button" onClick={handleCreateGame}>
        Create Game
      </button>

      </div>

      {/* Join Existing Game Section */}
      <div className="enter-game-container">
        <h2 className="game-creator-title">Enter Game</h2>

        <input
          type="text"
          className="input-field"
          maxLength="6"
          placeholder="Game Code"
          value={gameCode}
          onChange={(e) => setGameCode(e.target.value)}
        />

        <input
          type="text"
          className="input-field"
          maxLength="15"
          placeholder="Player Name"
          value={playerName}
          onChange={(e) => setPlayerName(e.target.value)}
        />

        <button className="enter-button" onClick={handleEnterGame}>
          Enter Game
        </button>
      </div>
    </div>
  );
};

export default GameCreator;





