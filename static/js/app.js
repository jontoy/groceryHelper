const $toastBody = $('.toast-body');

const findCorrectElement = (classIdentifier, startingElement, maxDepth=4) => {
    let depth = 0;
    target = startingElement;
    while (!target.classList.contains(classIdentifier) && (depth <= maxDepth)){
        target = target.parentElement;
        depth += 1;
    }
    if (target.classList.contains(classIdentifier)){
        return target
    }
}

$(document.body).on('click', '.add-to-cart', async (e) => {
    e.preventDefault();
    const target = findCorrectElement('add-to-cart', e.target);
    if (target){
        const recipeId = target.dataset.recipeId;
        try{
            const res = await axios.post(`/api/recipes/${recipeId}/add-to-cart`);
            $toastBody.text(`${res.data.message}`);
            const targetCard = findCorrectElement('card', target);
            shoppingCartIcon = targetCard.querySelector('.fa-shopping-cart');
            shoppingCartIcon.classList.add('text-secondary');
            shoppingCartIcon.classList.remove('text-light');
            $('.toast').addClass('bg-success');
            $('.toast').removeClass('bg-danger');
            $('.toast').removeClass('hidden');
            $('.toast').toast('show');
        } catch (error) {
            $toastBody.text(`${error.response.data.message}`);
            $('.toast').removeClass('bg-success');
            $('.toast').addClass('bg-danger');

        }
        $('.toast').removeClass('hidden');
        $('.toast').toast('show');

    }
});

$(document.body).on('click', '.favorite', async (e) => {
    e.preventDefault();
    const target = findCorrectElement('favorite', e.target);
    if (target){
        const recipeId = target.dataset.recipeId;
        try{
            const res = await axios.post(`/api/recipes/${recipeId}/favorite`);
            target.setAttribute('class', 'unfavorite fas fa-heart text-danger');
            $toastBody.text(`${res.data.message}`);
            $('.toast').addClass('bg-success');
            $('.toast').removeClass('bg-danger');
            $('.toast').removeClass('hidden');
            $('.toast').toast('show');
        } catch (error) {
            $toastBody.text(`${error.response.data.message}`);
            $('.toast').removeClass('bg-success');
            $('.toast').addClass('bg-danger');

        }
        $('.toast').removeClass('hidden');
        $('.toast').toast('show');

    }
});

$(document.body).on('click', '.unfavorite', async (e) => {
    e.preventDefault();
    const target = findCorrectElement('unfavorite', e.target);
    if (target){
        const recipeId = target.dataset.recipeId;
        try{
            const res = await axios.post(`/api/recipes/${recipeId}/unfavorite`);
            $toastBody.text(`${res.data.message}`);
            target.setAttribute('class', 'favorite far fa-heart text-secondary')
            $('.toast').addClass('bg-success');
            $('.toast').removeClass('bg-danger');
            $('.toast').removeClass('hidden');
            $('.toast').toast('show');
        } catch (error) {
            $toastBody.text(`${error.response.data.message}`);
            $('.toast').removeClass('bg-success');
            $('.toast').addClass('bg-danger');

        }
        $('.toast').removeClass('hidden');
        $('.toast').toast('show');

    }
});