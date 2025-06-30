from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, NumberRange

class ReadingRequestForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    birthdate = StringField('Data de Nascimento (dd/mm/aaaa)', validators=[DataRequired()])
    question = TextAreaField('Sua Pergunta (seja o mais específico possível)', validators=[DataRequired(), Length(min=10, max=500)])
    spread_type = SelectField('Tipo de Leitura', choices=[
        ('three_card', 'Três Cartas - Passado, Presente, Futuro'),
        ('celtic_cross', 'Cruz Celta - Uma visão abrangente'),
        ('relationship', 'Relacionamento - Foco em um relacionamento específico'),
        ('career', 'Carreira - Orientação profissional'),
        ('yes_no', 'Sim/Não - Para perguntas diretas')
    ], validators=[DataRequired()])
    payment_method = SelectField('Método de Pagamento', choices=[('paypal', 'PayPal'), ('credit_card', 'Cartão de Crédito')], validators=[DataRequired()])
    submit = SubmitField('Solicitar Leitura')


class ContactForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Mensagem', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Enviar Mensagem')

class FeedbackForm(FlaskForm):
    rating = IntegerField('Avaliação (1-5 estrelas)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comments = TextAreaField('Comentários', validators=[Length(max=500)])
    submit = SubmitField('Enviar Feedback')