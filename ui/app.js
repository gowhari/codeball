(function() {

    'use strict';


    var ws;
    var canvas;
    var players;
    var ball;
    var field = {width: 25, height: 15, goal_size: 3};
    var scoreboard;
    var curr_time = 0;
    var score = [0, 0];


    var pr = function() {
        console.log.apply(console, arguments);
    };


    var canvas_x = function(x) {
        return x / field.width * canvas.width;
    };


    var canvas_y = function(y) {
        return y / field.height * canvas.height;
    };


    var init = function() {
        canvas = new fabric.Canvas(document.querySelector('canvas'));
        canvas.setBackgroundColor('green');
        var player_1_img = document.querySelector('.player-1');
        var player_2_img = document.querySelector('.player-2');
        players = [];
        for (var i = 0; i < 6; i++) {
            var p = new fabric.Image(i < 3 ? player_1_img : player_2_img, {left: 0, top: 0, originX: 'center', originY: 'center'});
            players.push(p);
            canvas.add(p);
        }
        var ball_img = document.querySelector('.ball');
        ball = new fabric.Image(ball_img, {left: 0, top: 0, originX: 'center', originY: 'center'});
        canvas.add(ball);
        var goal_1 = new fabric.Rect({left: 0, top: canvas_y(field.height / 2 - field.goal_size / 2), fill: '#fff', width: 5, height: canvas_y(field.goal_size)});
        var goal_2 = new fabric.Rect({left: canvas_x(field.width) - 5, top: canvas_y(field.height / 2 - field.goal_size / 2), fill: '#fff', width: 5, height: canvas_y(field.goal_size)});
        canvas.add(goal_1);
        canvas.add(goal_2);
        var ws = new WebSocket('ws://localhost:9000/view/NEW1');
        ws.onmessage = ws_onmessage;
        scoreboard = document.querySelector('.scoreboard');
    };


    var ws_onmessage = function(msg) {
        var msg = JSON.parse(msg.data);
        if (msg.message == 'state') {
            update_state(msg.data);
        }
        else if (msg.message == 'goal') {
            pr('Goal for: ' + msg.team);
        }
        else if (msg.message == 'field') {
            field = msg.data;
        }
    };


    var update_state = function(data) {
        for (var i = 0; i < 6; i++) {
            var p = i < 3 ? data.team0[i] : data.team1[i - 3];
            players[i].set({left: canvas_x(p.x), top: canvas_y(p.y)});
        }
        var b = data.ball;
        ball.set({left: canvas_x(b.x), top: canvas_y(b.y)});
        canvas.renderAll();
        update_scoreboard(data);
    };


    var update_scoreboard = function(data) {
        curr_time = data.time;
        score = data.score;
        var min = curr_time / 60 | 0;
        var sec = curr_time % 60 | 0;
        min = String(min).padStart(2, '0');
        sec = String(sec).padStart(2, '0');
        scoreboard.innerText = `${score[0]}-${score[1]} _ ${min}:${sec}`;
    };


    window.onload = init;

})();
