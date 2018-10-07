(function() {

    'use strict';


    var ws;
    var canvas;
    var players;
    var ball;
    var field = {width: 25, height: 15, goal_size: 3};
    var token;
    var scoreboard;
    var score = [0, 0];
    var t1 = new Date();


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
        var data = JSON.parse(msg.data);
            if (data.token != undefined) {
            token = data.token;
        }
        else if (data.state != undefined) {
            for (var i = 0; i < 6; i++) {
                    var d = i < 3 ? data.state['team-0'][i] : data.state['team-1'][i - 3];
                players[i].set({left: canvas_x(d.x), top: canvas_y(d.y)});
            }
            var d = data.state.ball;
            ball.set({left: canvas_x(d.x), top: canvas_y(d.y), angle: (ball.angle + 0) % 360});
            canvas.renderAll();
        }
        else if (data.goal) {
            score[data.team] += 1;
        }
        else if (data.field != undefined) {
            field = data.field;
        }
        var t2 = new Date();
        var t = (t2.getTime() - t1.getTime()) / 1000;
        var min = (t / 60 | 0) + '';
        var sec = (t % 60 | 0) + '';
        if (min.length == 1) min = '0' + min;
        if (sec.length == 1) sec = '0' + sec;
        scoreboard.innerText = min + ':' + sec + '  ' + score[0] + ' - ' + score[1];
    };


    window.onload = init;

})();
