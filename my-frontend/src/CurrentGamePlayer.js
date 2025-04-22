import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import "./CurrentGamePlayer.css"; // Ensure you style the new elements properly

const CurrentGamePlayer = () => {
  const { playerId } = useParams(); // Get the player ID from the URL
  const [player, setPlayer] = useState(null); // Store player data
  const [loading, setLoading] = useState(true); // Loading state
  const [actions, setActions] = useState([]); // Store actions
  const [information, setInformation] = useState([]); // Store information
  const [responses, setResponses] = useState({}); // Store responses input
  const [newInformation, setNewInformation] = useState(""); // New info input field

  const ipAddress = window.location.hostname;
  const apiUrl = `http://${ipAddress}:8000`;

  // Fetch player data from the backend
  useEffect(() => {
    const fetchPlayerData = async () => {
      try {
        const response = await fetch(`${apiUrl}/players/${playerId}`);
        const data = await response.json();
        if (data.result === "success") {
          setPlayer(data.player); // Set the player data
        } else {
          console.error("Player not found:", data.error);
        }
      } catch (error) {
        console.error("Error fetching player data:", error);
      } finally {
        setLoading(false); // Set loading to false once data is fetched
      }
    };

    fetchPlayerData();
  }, [playerId, apiUrl]);

  // Fetch actions and information
  const fetchPlayerActionsAndInfo = async () => {
    if (!player) return;

    try {
      const response = await fetch(`${apiUrl}/player_actions/${player.game_code}/${playerId}`);
      const data = await response.json();
      if (data.result === "success") {
        setActions(data.actions);
        setInformation(data.information);
      } else {
        console.error("No actions found:", data.error);
      }
    } catch (error) {
      console.error("Error fetching player actions and information:", error);
    }
  };

  const handleInputChangeSolo = (e) => {
    setNewInformation(e.target.value);
  };

  // Send new information to the backend
  const handleSendResponseSolo = async () => {
    if (!newInformation.trim()) return;

    const responseBody = {
      player_id: playerId,
      information_type: "custom",
      information_input: newInformation,
      response_required: false,
      turn: player.turn
    };

    try {
      const response = await fetch(`${apiUrl}/player/add_information`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(responseBody),
      });

      const data = await response.json();
      if (data.result === "success") {
        setNewInformation(""); // Clear input field
      } else {
        console.error("Error adding information:", data.error);
      }
      fetchPlayerActionsAndInfo()
    } catch (error) {
      console.error("Error sending information:", error);
    }
  };

  // Handle input change for required responses
  const handleInputChange = (infoId, event) => {
    setResponses({
      ...responses,
      [infoId]: event.target.value,
    });
  };

  // Handle send response button
  const handleSendResponse = async (infoId) => {
    const responseText = responses[infoId];
    if (!responseText) return;

    try {
      const response = await fetch(`${apiUrl}/player/add_action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_id: playerId,
          action_type: "response",
          action_input: responseText,
          response_required: false,
          turn: player.turn
        }),
      });

      const data = await response.json();
      if (data.result === "success") {
        setResponses({ ...responses, [infoId]: "" }); // Clear input after sending
      } else {
        console.error("Error sending response:", data.error);
      }
      fetchPlayerActionsAndInfo()
    } catch (error) {
      console.error("Failed to send response:", error);
    }
  };

  if (loading) {
    return <div>Loading player data...</div>; // Show loading text until data is fetched
  }

  if (!player) {
    return <div>Player not found.</div>; // Handle case when player is not found
  }

  return (
    <div className="current-game-container">
      <h1 className="game-creator-title">Player Dashboard</h1>
      <div className="player-info-container">
        <div className="player-info-item"><strong>Player ID:</strong> <span>{player.player_id}</span></div>
        <div className="player-info-item"><strong>Player Name:</strong> <span>{player.player_name}</span></div>
        <div className="player-info-item"><strong>Game Code:</strong> <span>{player.game_code}</span></div>
        {player.character && (
          <>
            <div className="player-info-item">
              <strong>Character Name:</strong> <span>{player.character.character_name}</span>
            </div>
            <div className="player-info-item">
              <strong>Character Description:</strong> <span>{player.character.character_description}</span>
            </div>
            <div className="player-info-item">
              <strong>Designation:</strong> <span>{player.character.designation}</span>
            </div>
          </>
        )}
        <div className="player-info-item"><strong>Character ID:</strong> <span>{player.character_id}</span></div>
        <div className="player-info-item"><strong>Vote Token Remaining:</strong> <span>{player.vote_token_remaining ? "Yes" : "No"}</span></div>
        <div className="player-info-item"><strong>Creation Date:</strong> <span>{new Date(player.creation_date).toLocaleString()}</span></div>
      </div>

      {/* Refresh Button */}
      <button className="refresh-button" onClick={fetchPlayerActionsAndInfo}>
        Refresh Actions & Information
      </button>

      {/* Actions and Information Section */}
      <div className="actions-info-container">
        <h2>Actions</h2>
        {actions.length === 0 ? <p>No actions available.</p> : (
          actions.map(action => (
            <div key={action.action_id} className="action-item">
              <p><strong>Type:</strong> {action.action_type}</p>
              <p><strong>Input:</strong> {action.action_input}</p>
              <p><strong>Turn:</strong> {action.turn}</p>
              <p><strong>Response Required:</strong> {action.response_required ? "Yes" : "No"}</p>
            
            {action.response_required && (
            <div className="response-section">
                <input
                type="text"
                placeholder="Enter response..."
                value={responses[action.action_id] || ""}
                onChange={(e) => handleInputChange(action.action_id, e)}
                />
                <button onClick={() => handleSendResponse(action.action_id)}>Send</button>
            </div>
            )}
            
            </div>
          ))
        )}

        <h2>Information</h2>
        {information.length === 0 ? <p>No New Info</p> : (
          information.map(info => (
            <div key={info.information_id} className="info-item">
              <p><strong>Type:</strong> {info.information_type}</p>
              <p><strong>Details:</strong> {info.information_input}</p>
              <p><strong>Turn:</strong> {info.turn}</p>
              <p><strong>Response Required:</strong> {info.response_required ? "Yes" : "No"}</p>

            </div>
          ))
        )
        }
        {/* New Information Input */}
        <h4>Ask any questions below</h4>
        <div className="response-section">
            <input
            type="text"
            placeholder="Enter comment..."
            value={newInformation}
            onChange={handleInputChangeSolo}
            />
            <button onClick={handleSendResponseSolo}>Send</button>
        </div>
      </div>
    </div>
  );
};

export default CurrentGamePlayer;

