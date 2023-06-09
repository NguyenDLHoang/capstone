function submit(data) {
    var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value
    $.ajax({
        url: "/tasks/edit", 
        type: "POST",
        headers: {
            'X-CSRFToken': csrftoken,
        },
        data: data,
        dataType: 'json',
    });
}

$('#edit').click(function(event) {
    event.preventDefault();
    submit();
    location.reload()
})


function addComment(data) {
    var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value
    $.ajax({
        url: "/tasks/edit", 
        type: "POST",
        headers: {
            'X-CSRFToken': csrftoken,
        },
        data: data,
        dataType: 'json',
    });
}

$('#comment-button').click(function(event) {
    event.preventDefault();
    data = {
        content: $(['name^=content'])[0].value,
    }
    addComment(data);
    location.reload()
})
